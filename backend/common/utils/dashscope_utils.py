import os
import logging
from typing import Optional

from common.config import get_settings

logger = logging.getLogger(__name__)

def get_dashscope_http_api_url() -> str:
    """Resolve DashScope HTTP API base URL for uploads and ASR tasks."""
    settings = get_settings()
    base_url = settings.api.dashscope_http_api_url or "https://dashscope.aliyuncs.com/api/v1"
    return base_url.rstrip("/")


def upload_to_dashscope(file_path: str, api_key: str, model: str = "qwen-vl-max") -> Optional[str]:
    """
    Upload a file to DashScope temporary storage and get a public URL.
    
    The URL is valid for 48 hours.
    Uses the official DashScope SDK's OssUtils for reliable uploads.
    
    Args:
        file_path: Local file path
        api_key: DashScope API key
        model: Model name context (default: qwen-vl-max, use 'emoji-v1' or 'fun-asr' if needed)
        
    Returns:
        Public oss:// URL for the uploaded file, or None if failed
    """
    try:
        import dashscope
        # Configure SDK HTTP API base BEFORE importing OssUtils
        dashscope.base_http_api_url = get_dashscope_http_api_url()
        
        from dashscope.utils.oss_utils import OssUtils
        
        # Upload the file using DashScope's OSS utility directly
        # This returns an oss:// URL that's accessible by DashScope services
        oss_url, _ = OssUtils.upload(
            model=model,
            file_path=file_path,
            api_key=api_key
        )
        
        if oss_url:
            logger.info(f"File uploaded to DashScope OSS: {oss_url[:80] if len(oss_url) > 80 else oss_url}")
            return oss_url
        else:
            logger.error("OssUtils.upload returned None")
            return None
            
    except Exception as e:
        logger.error(f"DashScope OSS upload error: {e}")
        # Only print trace in debug/dev
        if os.environ.get('DEBUG'):
            import traceback
            traceback.print_exc()
        return None
