"""
Cloudinary image upload service
"""
import cloudinary
import cloudinary.uploader
from app.config import settings
from typing import Optional

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def upload_image(
    file_content: bytes,
    folder: str = "odyssey",
    public_id: Optional[str] = None
) -> str:
    """
    Upload an image to Cloudinary

    Args:
        file_content: Image file content as bytes
        folder: Cloudinary folder name
        public_id: Optional public ID for the image

    Returns:
        Cloudinary URL of uploaded image

    Raises:
        Exception: If upload fails
    """
    try:
        upload_result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )

        return upload_result.get("secure_url")

    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")


def delete_image(public_id: str) -> bool:
    """
    Delete an image from Cloudinary

    Args:
        public_id: Public ID of the image to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False
