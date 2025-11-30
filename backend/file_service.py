import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        # Local storage directory
        self.storage_dir = Path("/app/backend/uploads")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage initialized at {self.storage_dir}")
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> Dict[str, Any]:
        """Save file to local storage."""
        try:
            # Generate unique filename
            file_ext = Path(filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Create category directory
            category_dir = self.storage_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Save file
            file_path = category_dir / unique_filename
            file_path.write_bytes(file_content)
            
            # Generate accessible URL (relative path)
            file_url = f"/uploads/{category}/{unique_filename}"
            
            logger.info(f"File saved: {filename} -> {file_path}")
            
            return {
                "success": True,
                "file_url": file_url,
                "original_filename": filename,
                "stored_filename": unique_filename,
                "size": len(file_content)
            }
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, file_url: str) -> Dict[str, Any]:
        """Delete file from storage."""
        try:
            # Extract path from URL
            if file_url.startswith("/uploads/"):
                relative_path = file_url.replace("/uploads/", "")
                file_path = self.storage_dir / relative_path
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"File deleted: {file_path}")
                    return {"success": True}
            
            return {"success": False, "error": "File not found"}
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_file_path(self, file_url: str) -> Optional[Path]:
        """Get actual file path from URL."""
        if file_url.startswith("/uploads/"):
            relative_path = file_url.replace("/uploads/", "")
            file_path = self.storage_dir / relative_path
            if file_path.exists():
                return file_path
        return None

# Global file service instance
file_service = FileService()