"""
Photo service for image capture, storage, and processing
"""

from PIL import Image
import io
import os
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException

from app.core.config import settings


class PhotoService:
    """Service for photo handling and storage"""
    
    def __init__(self):
        self.storage_type = settings.PHOTO_STORAGE_TYPE
        self.max_size_mb = settings.PHOTO_MAX_SIZE_MB
        self.allowed_extensions = settings.PHOTO_ALLOWED_EXTENSIONS
        
        # Create local storage directory
        if self.storage_type == "local":
            os.makedirs("app/storage/photos", exist_ok=True)
    
    async def validate_photo(self, photo: UploadFile) -> None:
        """
        Validate uploaded photo
        
        Args:
            photo: Uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file extension
        ext = os.path.splitext(photo.filename)[1].lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}"
            )
        
        # Check file size
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        while chunk := await photo.read(chunk_size):
            file_size += len(chunk)
            if file_size > self.max_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_size_mb}MB"
                )
        
        # Reset file pointer
        await photo.seek(0)
    
    async def store_photo(
        self,
        photo: UploadFile,
        employee_id: str,
        photo_type: str  # 'check_in' or 'check_out'
    ) -> str:
        """
        Store photo and return URL
        
        Args:
            photo: Uploaded file
            employee_id: Employee UUID
            photo_type: Type of photo (check_in/check_out)
            
        Returns:
            URL or path to stored photo
        """
        # Validate
        await self.validate_photo(photo)
        
        # Read file
        contents = await photo.read()
        
        # Process image
        image = Image.open(io.BytesIO(contents))
        
        # Resize if needed
        image = self.resize_image(image, max_width=1024)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{employee_id}/{photo_type}_{timestamp}.jpg"
        
        # Convert to JPEG and compress
        img_byte_arr = io.BytesIO()
        
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
        img_byte_arr.seek(0)
        
        if self.storage_type == 'local':
            # Save to local filesystem
            filepath = f"app/storage/photos/{filename}"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(img_byte_arr.getvalue())
            
            return f"/static/photos/{filename}"
        
        elif self.storage_type == 's3':
            # Upload to S3
            return await self._upload_to_s3(img_byte_arr, filename)
        
        else:
            raise ValueError(f"Invalid storage type: {self.storage_type}")
    
    async def _upload_to_s3(self, file_obj: io.BytesIO, filename: str) -> str:
        """
        Upload file to S3
        
        Args:
            file_obj: File object to upload
            filename: Destination filename
            
        Returns:
            S3 URL
        """
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            s3_client.upload_fileobj(
                file_obj,
                settings.S3_BUCKET,
                f"photos/{filename}",
                ExtraArgs={
                    'ContentType': 'image/jpeg',
                    'ACL': 'private'  # Keep photos private
                }
            )
            
            # Generate URL (presigned for private access)
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET,
                    'Key': f"photos/{filename}"
                },
                ExpiresIn=3600 * 24 * 90  # 90 days
            )
            
            return url
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to S3: {str(e)}"
            )
    
    @staticmethod
    def resize_image(
        image: Image.Image,
        max_width: int = 1024,
        max_height: int = 1024
    ) -> Image.Image:
        """
        Resize image while maintaining aspect ratio
        
        Args:
            image: PIL Image object
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized image
        """
        width, height = image.size
        
        # Calculate scaling factor
        scale = min(max_width / width, max_height / height, 1.0)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def delete_photo(self, photo_url: str) -> bool:
        """
        Delete photo from storage
        
        Args:
            photo_url: URL or path to photo
            
        Returns:
            True if successful
        """
        if self.storage_type == 'local':
            # Extract path from URL
            path = photo_url.replace('/static/', 'app/storage/')
            
            try:
                if os.path.exists(path):
                    os.remove(path)
                return True
            except Exception as e:
                print(f"Failed to delete photo: {e}")
                return False
        
        elif self.storage_type == 's3':
            # Delete from S3
            try:
                import boto3
                
                s3_client = boto3.client('s3')
                
                # Extract key from URL
                key = photo_url.split(f"{settings.S3_BUCKET}.s3.amazonaws.com/")[1]
                
                s3_client.delete_object(
                    Bucket=settings.S3_BUCKET,
                    Key=key
                )
                
                return True
                
            except Exception as e:
                print(f"Failed to delete from S3: {e}")
                return False
        
        return False
    
    async def verify_face(
        self,
        check_in_photo_url: str,
        reference_photo_url: str,
        threshold: float = 0.6
    ) -> dict:
        """
        Optional: Verify if person in check-in photo matches reference
        This is an advanced feature that can be added later
        
        Args:
            check_in_photo_url: URL to check-in photo
            reference_photo_url: URL to reference photo
            threshold: Similarity threshold (0-1)
            
        Returns:
            Dict with match result and confidence
        """
        # This would use face_recognition library or similar
        # For now, return a placeholder
        
        return {
            "match": True,
            "confidence": 0.85,
            "method": "placeholder"
        }


# Create singleton instance
photo_service = PhotoService()
