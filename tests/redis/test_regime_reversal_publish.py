"""Unit tests for regime Redis SET + ZSET reversal → XADD."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from stream.redis_stream_handler import RedisStreamHandler  # noqa: E402


@pytest.fixture
def handler(monkeypatch):
    from config import settings as settings_mod

    h = RedisStreamHandler.__new__(RedisStreamHandler)
    h.stream_name = "signals"
    h.redis_client = MagicMock()
    h.redis_client.zrangebyscore.return_value = []
    h.redis_client.zrange.return_value = []
    h.redis_client.get.return_value = None
    h.redis_client.xadd.return_value = "1-0"
    monkeypatch.setattr(settings_mod.config, "REDIS_REGIME_REVERSAL_CONFIRM", 2, raising=False)
    monkeypatch.setattr(settings_mod.config, "REDIS_REGIME_MIN_CONFIDENCE", 0.65, raising=False)
    monkeypatch.setattr(settings_mod.config, "REDIS_REGIME_WINDOW_HOURS", 48, raising=False)
    monkeypatch.setattr(settings_mod.config, "REDIS_REGIME_STREAM", "regime_signals", raising=False)
    monkeypatch.setattr(
        settings_mod.config, "REDIS_REGIME_CURRENT_PREFIX", "regime:current", raising=False
    )
    monkeypatch.setattr(
        settings_mod.config, "REDIS_REGIME_ZWIN_PREFIX", "regime:zwin", raising=False
    )
    monkeypatch.setattr(
        settings_mod.config,
        "REDIS_REGIME_LAST_REVERSAL_PREFIX",
        "regime:last_reversal",
        raising=False,
    )
    return h


def _point(ts, regime, conf=0.7):
    return json.dumps(
        {
            "timestamp": ts,
            "regime": regime,
            "regime_label": {1: "TREND_UP", 2: "TREND_DOWN", 3: "RANGE"}[regime],
            "confidence": conf,
            "price": 1000,
            "recommended_strategy": "default",
        },
        separators=(",", ":"),
    )


def test_sets_current_without_xadd_when_no_reversal(handler):
    handler.redis_client.zrange.return_value = [
        _point(1, 1),
        _point(2, 1),
    ]
    out = handler.publish_regime(
        {
            "timestamp": 3,
            "inst_id": "ETH-USDT-SWAP",
            "regime": 1,
            "regime_label": "TREND_UP",
            "confidence": 0.8,
            "price": 1900,
            "probabilities": {1: 0.8, 2: 0.1, 3: 0.1},
        }
    )
    assert out["updated_current"] is True
    assert out["reversal_alerted"] is False
    assert handler.redis_client.set.call_args_list[0][0][0] == "regime:current:ETH-USDT-SWAP"
    handler.redis_client.zadd.assert_called()
    handler.redis_client.xadd.assert_not_called()


def test_xadd_on_up_to_down_reversal(handler):
    # window after zadd will be read via zrange — include the new point
    handler.redis_client.zrange.return_value = [
        _point(100, 1, 0.8),
        _point(200, 1, 0.8),
        _point(300, 2, 0.8),
        _point(400, 2, 0.8),
    ]
    out = handler.publish_regime(
        {
            "timestamp": 400,
            "inst_id": "ETH-USDT-SWAP",
            "regime": 2,
            "regime_label": "TREND_DOWN",
            "confidence": 0.8,
            "price": 1800,
            "recommended_strategy": "default_short",
            "probabilities": {1: 0.1, 2: 0.8, 3: 0.1},
        }
    )
    assert out["reversal_detected"] is True
    assert out["reversal_alerted"] is True
    assert out["stream_id"] == "1-0"
    assert out["reversal"]["from_regime"] == 1
    assert out["reversal"]["to_regime"] == 2
    handler.redis_client.xadd.assert_called_once()
    args, kwargs = handler.redis_client.xadd.call_args
    assert args[0] == "regime_signals"
    assert args[1]["type"] == "regime_reversal"


def test_no_duplicate_alert(handler):
    handler.redis_client.zrange.return_value = [
        _point(100, 1, 0.8),
        _point(300, 2, 0.8),
        _point(400, 2, 0.8),
    ]
    # already alerted this streak
    handler.redis_client.get.return_value = "1:2:300"
    out = handler.publish_regime(
        {
            "timestamp": 400,
            "inst_id": "ETH-USDT-SWAP",
            "regime": 2,
            "regime_label": "TREND_DOWN",
            "confidence": 0.8,
            "price": 1800,
        }
    )
    assert out["reversal_detected"] is True
    assert out["reversal_alerted"] is False
    handler.redis_client.xadd.assert_not_called()


def test_detect_ignores_range_and_low_confidence(handler):
    points = handler._parse_window_members(
        [
            _point(1, 1, 0.9),
            _point(2, 3, 0.9),  # RANGE skipped
            _point(3, 2, 0.4),  # low conf skipped
            _point(4, 2, 0.9),
            _point(5, 2, 0.9),
        ]
    )
    rev = handler._detect_trend_reversal(points)
    assert rev is not None
    assert rev["from_regime"] == 1
    assert rev["to_regime"] == 2
    assert rev["confirm_count"] == 2


def test_dual_payload_sets_present_and_outlook(handler):
    handler.redis_client.zrange.return_value = []
    out = handler.publish_regime(
        {
            "timestamp": 500,
            "inst_id": "ETH-USDT-SWAP",
            "horizon_hours": 48,
            "present": {
                "regime": 1,
                "regime_label": "TREND_UP",
                "source": "rules",
                "recommended_strategy": "default",
            },
            "outlook_48h": {
                "regime": 3,
                "regime_label": "RANGE",
                "source": "model",
                "confidence": 0.72,
                "probabilities": {1: 0.2, 2: 0.08, 3: 0.72},
            },
            "derived": {"continues": False, "changes": True},
            # flat legacy = outlook
            "regime": 3,
            "regime_label": "RANGE",
            "confidence": 0.72,
            "price": 2000,
        }
    )
    assert out["updated_current"] is True
    stored = json.loads(handler.redis_client.set.call_args[0][1])
    assert stored["present"]["regime"] == 1
    assert stored["outlook_48h"]["regime"] == 3
    assert stored["derived"]["changes"] is True
    zmember = list(handler.redis_client.zadd.call_args[0][1].keys())[0]
    zobj = json.loads(zmember)
    # zwin tracks present structure for UP↔DOWN reversal
    assert zobj["regime"] == 1
    assert zobj["outlook_regime"] == 3


def test_transition_alert_requires_model_gate(handler):
    handler.redis_client.zrange.return_value = []
    handler.redis_client.get.return_value = None
    payload = {
        "timestamp": 600,
        "inst_id": "ETH-USDT-SWAP",
        "present": {"regime": 3, "regime_label": "RANGE", "source": "rules"},
        "transition": {
            "prediction": "CHANGE",
            "changes": True,
            "p_change": 0.8,
            "threshold": 0.7,
            "horizon_hours": 12,
            "model_gate_passed": True,
            "alert_eligible": True,
        },
        "derived": {
            "changes": True,
            "continues": False,
            "p_change": 0.8,
        },
        "regime": 3,
        "regime_label": "RANGE",
        "price": 2000,
    }
    out = handler.publish_regime(payload)
    assert out["transition_alerted"] is True
    args, _kwargs = handler.redis_client.xadd.call_args
    assert args[1]["type"] == "regime_change_risk"


def test_transition_alert_blocked_when_gate_failed(handler):
    handler.redis_client.zrange.return_value = []
    payload = {
        "timestamp": 601,
        "inst_id": "ETH-USDT-SWAP",
        "present": {"regime": 3, "regime_label": "RANGE"},
        "transition": {
            "prediction": "CHANGE",
            "changes": True,
            "p_change": 0.9,
            "threshold": 0.7,
            "model_gate_passed": False,
            "alert_eligible": False,
        },
        "derived": {"changes": True, "continues": False, "p_change": 0.9},
        "regime": 3,
        "regime_label": "RANGE",
    }
    out = handler.publish_regime(payload)
    assert out["transition_alerted"] is False
    handler.redis_client.xadd.assert_not_called()
