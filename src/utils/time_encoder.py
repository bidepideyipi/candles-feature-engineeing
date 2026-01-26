import pandas as pd
import numpy as np
from .calculator_interface import BaseTechnicalCalculator

class TimestampEncoder(BaseTechnicalCalculator):
    """Timestamp encoder for technical analysis"""
    
    def calculate(self, timestamps: list) -> pd.Series: 
        # Extract hours from timestamps
        if isinstance(timestamps[0], (int, float)):
            # Unix timestamps
            hours = [pd.to_datetime(ts, unit='s').hour for ts in timestamps]
        else:
            # Datetime objects
            hours = [ts.hour for ts in timestamps]
        
        # Convert to radians (24 hours = 2π radians)
        hours_rad = np.array(hours) * (2 * np.pi / 24)
        
        # Calculate cyclical features
        hour_cos = np.cos(hours_rad)
        hour_sin = np.sin(hours_rad)
        
        return hour_cos, hour_sin

TIMESTAMP_ENCODER = TimestampEncoder()
