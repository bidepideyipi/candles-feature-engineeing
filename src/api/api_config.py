"""
Configuration management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from collect.config_handler import config_handler
from config.settings import config
from typing import Dict, Any

router = APIRouter(prefix="/config", tags=["config"])


@router.post("")
def save_config(
    item: str = Query(..., description="配置项（如 smtp.qq.com）"),
    key: str = Query(..., description="配置键（如 account, authCode）"),
    value: str = Query(..., description="配置值"),
    desc: str = Query("", description="配置描述")
) -> Dict[str, Any]:
    """
    保存配置
    
    Args:
        item: 配置项 (e.g., "smtp.qq.com")
        key: 配置键 (e.g., "account", "authCode")
        value: 配置值
        desc: 配置描述
        
    Returns:
        {"success": bool, "message": str}
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    try:
        result = config_handler.save_config(item=item, key=key, value=value, desc=desc)
        if result:
            return {"success": True, "message": f"配置已保存: {item}.{key}"}
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置错误: {str(e)}")


@router.get("")
def get_config(
    item: str = Query(..., description="配置项（如 smtp.qq.com）"),
    key: str = Query(..., description="配置键（如 account, authCode）")
) -> Dict[str, Any]:
    """
    获取配置
    
    Args:
        item: 配置项 (e.g., "smtp.qq.com")
        key: 配置键 (e.g., "account", "authCode")
        
    Returns:
        {"item": str, "key": str, "value": str}
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    try:
        value = config_handler.get_config(item=item, key=key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"配置不存在: {item}.{key}")
        
        return {"item": item, "key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置错误: {str(e)}")


@router.get("/list")
def list_configs(item: str = Query(None, description="按配置项过滤")) -> Dict[str, Any]:
    """
    列出所有配置
    
    Args:
        item: 可选，按配置项过滤
        
    Returns:
        {"configs": List[Dict[str, Any]]}
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    try:
        configs = config_handler.list_configs(item=item)
        return {"configs": configs, "count": len(configs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出配置错误: {str(e)}")


@router.delete("")
def delete_config(
    item: str = Query(..., description="配置项（如 smtp.qq.com）"),
    key: str = Query(..., description="配置键（如 account, authCode）")
) -> Dict[str, Any]:
    """
    删除配置
    
    Args:
        item: 配置项 (e.g., "smtp.qq.com")
        key: 配置键 (e.g., "account", "authCode")
        
    Returns:
        {"success": bool, "message": str}
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    try:
        result = config_handler.delete_config(item=item, key=key)
        if result:
            return {"success": True, "message": f"配置已删除: {item}.{key}"}
        else:
            raise HTTPException(status_code=404, detail=f"配置不存在: {item}.{key}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除配置错误: {str(e)}")
