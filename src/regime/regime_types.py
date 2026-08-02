from enum import IntEnum


class MarketRegime(IntEnum):
    TREND_UP = 1
    TREND_DOWN = 2
    RANGE = 3


REGIME_LABELS = {
    MarketRegime.TREND_UP: "TREND_UP",
    MarketRegime.TREND_DOWN: "TREND_DOWN",
    MarketRegime.RANGE: "RANGE",
}

REGIME_STRATEGY = {
    MarketRegime.TREND_UP: "default",
    MarketRegime.TREND_DOWN: "default_short",
    MarketRegime.RANGE: "grid",
}

REGIME_DESCRIPTION = {
    MarketRegime.TREND_UP: "Uptrend structure → trend-following long bias",
    MarketRegime.TREND_DOWN: "Downtrend structure → short / defensive bias",
    MarketRegime.RANGE: "Range structure → grid / mean-reversion bias",
}

REGIME_HORIZON_HOURS_DEFAULT = 48
MS_PER_HOUR = 60 * 60 * 1000
