import os
import logging
import json
import uuid
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from django.conf import settings as django_settings

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)

class FileASRService:
    """Service for handling File ASR/Translation tasks using Groq API."""
    
    @staticmethod
    def _run_groq_transcription(task_id: str, file_path: str, api_key: str, model: str):
        """Background worker for Groq transcription"""
        upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_results'
        upload_dir.mkdir(parents=True, exist_ok=True)
        result_path = upload_dir / f"{task_id}.json"
        
        try:
            if not Groq:
                raise ImportError("groq package not installed")

            client = Groq(api_key=api_key)
            
            logger.info(f"Starting Groq transcription for task {task_id}, file: {file_path}")
            
            with open(file_path, "rb") as file:
                # Call Groq API
                transcription = client.audio.transcriptions.create(
                  file=(os.path.basename(file_path), file.read()),
                  model=model,
                  response_format="json",
                  temperature=0.0
                )
            
            text = transcription.text
            logger.info(f"Groq transcription completed for {task_id}")
            
            result_data = {
                "task_id": task_id,
                "status": "SUCCEEDED",
                "task_type": "transcription",
                "full_text": text,
                "results": [{
                    "file_url": "local",
                    "transcription_url": None,
                    "text": text,
                    "status": "SUCCEEDED"
                }]
            }
            
            with open(result_path, "w") as f:
                json.dump(result_data, f)
                
        except Exception as e:
            logger.error(f"Groq transcription failed for {task_id}: {e}")
            error_data = {
                "task_id": task_id,
                "status": "FAILED",
                "task_type": "transcription",
                "message": str(e),
                "error_message": str(e)
            }
            with open(result_path, "w") as f:
                json.dump(error_data, f)

    @staticmethod
    def _run_groq_translation(task_id: str, file_path: str, api_key: str, model: str):
        """Background worker for Groq translation (audio -> English)"""
        upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_results'
        upload_dir.mkdir(parents=True, exist_ok=True)
        result_path = upload_dir / f"{task_id}.json"
        
        try:
            if not Groq:
                raise ImportError("groq package not installed")

            client = Groq(api_key=api_key)
            
            logger.info(f"Starting Groq translation for task {task_id}, file: {file_path}")
            
            with open(file_path, "rb") as file:
                # Call Groq Translation API (outputs English)
                translation = client.audio.translations.create(
                  file=(os.path.basename(file_path), file.read()),
                  model=model,
                  response_format="json",
                  temperature=0.0
                )
            
            text = translation.text
            logger.info(f"Groq translation completed for {task_id}")
            
            result_data = {
                "task_id": task_id,
                "status": "SUCCEEDED",
                "task_type": "translation",
                "full_text": text,
                "results": [{
                    "file_url": "local",
                    "translation_url": None,
                    "text": text,
                    "status": "SUCCEEDED"
                }]
            }
            
            with open(result_path, "w") as f:
                json.dump(result_data, f)
                
        except Exception as e:
            logger.error(f"Groq translation failed for {task_id}: {e}")
            error_data = {
                "task_id": task_id,
                "status": "FAILED",
                "task_type": "translation",
                "message": str(e),
                "error_message": str(e)
            }
            with open(result_path, "w") as f:
                json.dump(error_data, f)

    @staticmethod
    def transcribe(file_path: str, api_key: str = None, model: str = None) -> Dict[str, Any]:
        """
        Submit file for transcription using Groq API (Async via Thread).
        Returns text in the original language.
        """
        # Default to configured key or env
        from common.config import get_settings
        settings = get_settings()
        api_key = api_key or settings.api.groq_api_key or os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            return {"success": False, "error_message": "GROQ_API_KEY is not configured"}
            
        # Default model if not provided
        model = model or settings.api.groq_asr_model
        
        # Create Task ID
        task_id = f"groq-trans-{uuid.uuid4().hex}"
        
        # Start background thread
        thread = threading.Thread(
            target=FileASRService._run_groq_transcription,
            args=(task_id, file_path, api_key, model)
        )
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "task_id": task_id,
            "task_type": "transcription",
            "status": "PENDING"
        }

    @staticmethod
    def translate(file_path: str, api_key: str = None, model: str = None) -> Dict[str, Any]:
        """
        Submit file for translation using Groq API (Async via Thread).
        Translates audio into English.
        """
        # Default to configured key or env
        from common.config import get_settings
        settings = get_settings()
        api_key = api_key or settings.api.groq_api_key or os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            return {"success": False, "error_message": "GROQ_API_KEY is not configured"}
            
        # Default model if not provided
        model = model or settings.api.groq_asr_model
        
        # Create Task ID
        task_id = f"groq-transl-{uuid.uuid4().hex}"
        
        # Start background thread
        thread = threading.Thread(
            target=FileASRService._run_groq_translation,
            args=(task_id, file_path, api_key, model)
        )
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "task_id": task_id,
            "task_type": "translation",
            "status": "PENDING"
        }

    @staticmethod
    def get_task_result(task_id: str, api_key: str = None) -> Dict[str, Any]:
        """
        Check task status by reading the local result file.
        """
        try:
            upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_results'
            result_path = upload_dir / f"{task_id}.json"
            
            if not result_path.exists():
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": "PENDING"
                }
            
            with open(result_path, "r") as f:
                data = json.load(f)
                
            return {
                "success": True,
                **data
            }
                
        except Exception as e:
            logger.error(f"Task result fetch exception: {e}")
            return {"success": False, "error_message": str(e)}
