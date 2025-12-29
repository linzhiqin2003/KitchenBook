"""
Emoji Service - Handles face detection and emoji video generation

This service integrates with Alibaba DashScope API to:
1. Detect faces in portrait images (emoji-detect-v1)
2. Generate emoji videos from detected faces (emoji-v1)
"""

import os
import time
import logging
import requests
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


@dataclass
class FaceDetectionResult:
    """Result from face detection API"""
    success: bool
    bbox_face: Optional[List[int]] = None  # [x1, y1, x2, y2]
    ext_bbox_face: Optional[List[int]] = None  # [x1, y1, x2, y2]
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class VideoGenerationResult:
    """Result from video generation API"""
    success: bool
    task_id: Optional[str] = None
    task_status: Optional[str] = None
    video_url: Optional[str] = None
    video_duration: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None


# Available emoji templates
# Available emoji templates
# Updated based on official documentation images (2025-12-28)
EMOJI_TEMPLATES = [
    # 萌娃系列 (Cute Kid)
    {"id": "mengwa_kaixin", "name": "萌娃·开心", "category": "萌娃", "desc": "哈哈哈"},
    {"id": "mengwa_dengyan", "name": "萌娃·瞪眼", "category": "萌娃", "desc": "我滴妈呀"},
    {"id": "mengwa_gandong", "name": "萌娃·感动", "category": "萌娃", "desc": "OK"},
    {"id": "mengwa_renzhen_1", "name": "萌娃·认真", "category": "萌娃", "desc": "让我想想"},
    {"id": "mengwa_jidong", "name": "萌娃·激动", "category": "萌娃", "desc": "Oh my god"},
    {"id": "mengwa_kun_1", "name": "萌娃·困", "category": "萌娃", "desc": "困困困"},
    {"id": "mengwa_jiaoxie", "name": "萌娃·狡黠", "category": "萌娃", "desc": "嘿嘿嘿~~~"},

    # 职场系列 (Workplace)
    {"id": "dagong_zhuakuang", "name": "职场·抓狂", "category": "职场", "desc": "又要加班"},
    {"id": "dagong_wunai", "name": "职场·无奈", "category": "职场", "desc": "好吧好吧"},
    {"id": "dagong_weixiao", "name": "职场·微笑", "category": "职场", "desc": "保持微笑"},
    {"id": "dagong_ganji", "name": "职场·感激", "category": "职场", "desc": "拜托拜托"},
    {"id": "dagong_kaixin", "name": "职场·开心", "category": "职场", "desc": "明天不上班"},
    {"id": "dagong_yangwang", "name": "职场·仰望", "category": "职场", "desc": "针不搓"},
    {"id": "dagong_kunhuo", "name": "职场·困惑", "category": "职场", "desc": "不是吧阿sir"},

    # 经典系列 (Classic)
    {"id": "jingdian_tiaopi", "name": "经典·调皮", "category": "经典", "desc": "嘿嘿嘿"},
    {"id": "jingdian_deyi_1", "name": "经典·得意", "category": "经典", "desc": "夸我"},
    {"id": "jingdian_qidai", "name": "经典·期待", "category": "经典", "desc": "新学期加油"},
    {"id": "jingdian_landuo_1", "name": "经典·懒惰", "category": "经典", "desc": "下课了？"},
    {"id": "jingdian_xianqi", "name": "经典·嫌弃", "category": "经典", "desc": "就这??"},
    {"id": "jingdian_lei", "name": "经典·累", "category": "经典", "desc": "开学太累了"},
]


class EmojiService:
    """
    Service for generating emoji videos from portrait images.
    
    Usage:
        service = EmojiService()
        
        # Step 1: Detect face
        detection = service.detect_face(image_url)
        
        # Step 2: Generate video
        if detection.success:
            result = service.generate_video(
                image_url=image_url,
                face_bbox=detection.bbox_face,
                ext_bbox=detection.ext_bbox_face,
                driven_id="mengwa_kaixin"
            )
    """
    
    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the emoji service.
        
        Args:
            api_key: DashScope API key. If not provided, reads from DASHSCOPE_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required")
    
    def _get_headers(self, async_mode: bool = False) -> dict:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            # Enable OSS resource resolution for oss:// URLs from temporary uploads
            "X-DashScope-OssResourceResolve": "enable"
        }
        if async_mode:
            headers["X-DashScope-Async"] = "enable"
        return headers
    
    def detect_face(self, image_url: str, ratio: str = "1:1") -> FaceDetectionResult:
        """
        Detect face in an image for emoji generation.
        
        Args:
            image_url: Public URL of the portrait image (HTTP/HTTPS)
            ratio: Aspect ratio for detection, fixed as "1:1" for emoji
            
        Returns:
            FaceDetectionResult with bounding boxes if successful
        """
        url = f"{self.BASE_URL}/services/aigc/image2video/face-detect"
        
        payload = {
            "model": "emoji-detect-v1",
            "input": {
                "image_url": image_url
            },
            "parameters": {
                "ratio": ratio
            }
        }
        
        try:
            logger.info(f"Detecting face in image: {image_url[:50]}...")
            response = requests.post(url, json=payload, headers=self._get_headers())
            data = response.json()
            
            logger.debug(f"Face detection response: {data}")
            
            # Check for API errors
            if "code" in data or "message" in data.get("output", {}):
                output = data.get("output", {})
                return FaceDetectionResult(
                    success=False,
                    error_code=data.get("code") or output.get("code"),
                    error_message=data.get("message") or output.get("message"),
                    request_id=data.get("request_id")
                )
            
            # Successful detection
            output = data.get("output", {})
            return FaceDetectionResult(
                success=True,
                bbox_face=output.get("bbox_face"),
                ext_bbox_face=output.get("ext_bbox_face"),
                request_id=data.get("request_id")
            )
            
        except requests.RequestException as e:
            logger.error(f"Face detection request failed: {e}")
            return FaceDetectionResult(
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
    
    def create_video_task(
        self,
        image_url: str,
        face_bbox: List[int],
        ext_bbox: List[int],
        driven_id: str = "mengwa_kaixin"
    ) -> VideoGenerationResult:
        """
        Create an async video generation task.
        
        Args:
            image_url: Public URL of the portrait image
            face_bbox: Face bounding box from detection [x1, y1, x2, y2]
            ext_bbox: Extended expression area from detection [x1, y1, x2, y2]
            driven_id: Emoji template ID (see EMOJI_TEMPLATES)
            
        Returns:
            VideoGenerationResult with task_id for polling
        """
        url = f"{self.BASE_URL}/services/aigc/image2video/video-synthesis"
        
        payload = {
            "model": "emoji-v1",
            "input": {
                "image_url": image_url,
                "driven_id": driven_id,
                "face_bbox": face_bbox,
                "ext_bbox": ext_bbox
            }
        }
        
        try:
            logger.info(f"Creating video task with template: {driven_id}")
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(async_mode=True)
            )
            data = response.json()
            
            logger.debug(f"Video task creation response: {data}")
            
            # Check for errors
            if "code" in data:
                return VideoGenerationResult(
                    success=False,
                    error_code=data.get("code"),
                    error_message=data.get("message"),
                    request_id=data.get("request_id")
                )
            
            output = data.get("output", {})
            return VideoGenerationResult(
                success=True,
                task_id=output.get("task_id"),
                task_status=output.get("task_status"),
                request_id=data.get("request_id")
            )
            
        except requests.RequestException as e:
            logger.error(f"Video task creation failed: {e}")
            return VideoGenerationResult(
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
    
    def check_task_status(self, task_id: str) -> VideoGenerationResult:
        """
        Check the status of a video generation task.
        
        Args:
            task_id: Task ID from create_video_task
            
        Returns:
            VideoGenerationResult with current status and video URL if completed
        """
        url = f"{self.BASE_URL}/tasks/{task_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            data = response.json()
            
            logger.debug(f"Task status response: {data}")
            
            output = data.get("output", {})
            usage = data.get("usage", {})
            
            # Check for errors in response
            if output.get("code") or data.get("code"):
                return VideoGenerationResult(
                    success=False,
                    task_id=task_id,
                    task_status=output.get("task_status", "FAILED"),
                    error_code=output.get("code") or data.get("code"),
                    error_message=output.get("message") or data.get("message"),
                    request_id=data.get("request_id")
                )
            
            task_status = output.get("task_status")
            
            return VideoGenerationResult(
                success=(task_status == "SUCCEEDED"),
                task_id=output.get("task_id"),
                task_status=task_status,
                video_url=output.get("video_url"),
                video_duration=usage.get("video_duration"),
                request_id=data.get("request_id")
            )
            
        except requests.RequestException as e:
            logger.error(f"Task status check failed: {e}")
            return VideoGenerationResult(
                success=False,
                task_id=task_id,
                task_status="UNKNOWN",
                error_message=f"Request failed: {str(e)}"
            )
    
    def generate_video_sync(
        self,
        image_url: str,
        face_bbox: List[int],
        ext_bbox: List[int],
        driven_id: str = "mengwa_kaixin",
        poll_interval: int = 5,
        max_wait: int = 300
    ) -> VideoGenerationResult:
        """
        Generate video synchronously (blocking with polling).
        
        Args:
            image_url: Public URL of the portrait image
            face_bbox: Face bounding box from detection
            ext_bbox: Extended expression area from detection
            driven_id: Emoji template ID
            poll_interval: Seconds between status checks (default: 5)
            max_wait: Maximum seconds to wait (default: 300 = 5 minutes)
            
        Returns:
            VideoGenerationResult with video URL if successful
        """
        # Create task
        task_result = self.create_video_task(
            image_url=image_url,
            face_bbox=face_bbox,
            ext_bbox=ext_bbox,
            driven_id=driven_id
        )
        
        if not task_result.success or not task_result.task_id:
            return task_result
        
        task_id = task_result.task_id
        elapsed = 0
        
        # Poll for completion
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            status = self.check_task_status(task_id)
            logger.info(f"Task {task_id} status: {status.task_status} ({elapsed}s)")
            
            if status.task_status in ["SUCCEEDED", "FAILED", "CANCELED"]:
                return status
        
        # Timeout
        return VideoGenerationResult(
            success=False,
            task_id=task_id,
            task_status="TIMEOUT",
            error_message=f"Task did not complete within {max_wait} seconds"
        )
    
    @staticmethod
    def get_available_templates() -> List[dict]:
        """Get list of available emoji templates."""
        return EMOJI_TEMPLATES
    
    @staticmethod
    def get_templates_by_category() -> dict:
        """Get templates grouped by category."""
        categories = {}
        for template in EMOJI_TEMPLATES:
            cat = template["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)
        return categories
