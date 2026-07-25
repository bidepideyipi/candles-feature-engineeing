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
    MarketRegime.TREND_UP: "上升趋势 → Default 趋势做多",
    MarketRegime.TREND_DOWN: "下降趋势 → Default 做空/观望",
    MarketRegime.RANGE: "震荡 → Grid 网格",
}
