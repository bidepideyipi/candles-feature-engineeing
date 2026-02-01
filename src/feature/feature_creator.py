
import pandas as pd

from utils.normalization_encoder import NormalizationEncoder
from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.time_encoder import TIMESTAMP_ENCODER
from utils.impulse_calculator import IMPULSE_CALCULATOR

class FeatureCreator:
    
    def __init__(self):
        self.n_encoder = NormalizationEncoder()
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.ts_encoder = TIMESTAMP_ENCODER
        self.vi_calculator = IMPULSE_CALCULATOR
        
        
    def process_data(self, inst_id: str) -> pd.DataFrame:
        return None
