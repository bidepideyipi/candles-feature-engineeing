from fastapi import APIRouter, HTTPException
from typing import Optional
from collect.okex_fetcher import okex_fetcher
from collect.candlestick_handler import candlestick_handler

# Create router for OKEx fetching endpoints
router = APIRouter(prefix="/fetch", tags=["fetch"])

@router.get("/history-count")
def get_history_count(inst_id: str = "ETH-USDT-SWAP", bar: str = "1H"):
    """
    获取历史数据数量
    """
    count = candlestick_handler.count(inst_id=inst_id, bar=bar)
    if count is None:
        raise HTTPException(status_code=404, detail="No data found")
    return {
        "inst_id": inst_id,
        "bar": bar,
        "count": count
    }

@router.get("/pull-quick")
def pull_quick(inst_id: str = "ETH-USDT-SWAP"):
    """
    快速拉取最新数据
    """
    success = okex_fetcher.fetch_historical_data(inst_id=inst_id, bar="4H", max_records=100)
    if not success:
        raise HTTPException(status_code=404, detail="No data found")
    success = okex_fetcher.fetch_historical_data(inst_id=inst_id, bar="1H", max_records=100)
    if not success:
        raise HTTPException(status_code=404, detail="No data found")
    success = okex_fetcher.fetch_historical_data(inst_id=inst_id, bar="15m", max_records=100)
    if not success:
        raise HTTPException(status_code=404, detail="No data found")
    
    return {
        "inst_id": inst_id,
        "bar": "4H,1H,15m",
        "max_records": 100,
        "success": success
    }
        


@router.get("/pull-large")
def fetch_okex_data(
    inst_id: str = "ETH-USDT-SWAP",
    bar: str = "1H",
    max_records: int = 600,
    current_after: int = None
):
    """
    Fetch candlestick data from OKEx API.
    
    Args:
        inst_id: Instrument ID (e.g., ETH-USDT-SWAP)
        bar: Time interval (e.g., 1H, 15m, 4H)
        max_records: Number of records to fetch (max 100000)
        current_after: 时间戳，毫秒级
    
    Returns:
        Candlestick data from OKEx
    """
    try:
        # Validate parameters
        if max_records < 600 or max_records > 60000:
            raise HTTPException(status_code=400, detail="max_records must be between 600 and 60000")
        
        if bar not in ["15m", "1H", "4H", "1D"]:
            raise HTTPException(status_code=400, detail="Invalid bar parameter")
        
        # Fetch data from OKEx
        success = okex_fetcher.fetch_historical_data(inst_id=inst_id, bar=bar, max_records=max_records, current_after=current_after)
        
        if not success:
            raise HTTPException(status_code=404, detail="No data found")
        
        return {
            "inst_id": inst_id,
            "bar": bar,
            "max_records": max_records,
            "success": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
