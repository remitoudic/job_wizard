import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.core.config import settings

# Initialize Cloudinary configuration
cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)


class CloudinaryService:
    def upload_image(self, file_content: bytes, user_id: int) -> str:
        """
        Upload an image to Cloudinary and return the secure URL.
        """
        response = cloudinary.uploader.upload(
            file_content,
            folder="profile_pictures",
            public_id=f"user_{user_id}",
            overwrite=True,
        )
        return response.get("secure_url")

    def delete_image(self, url: str):
        """
        Delete an image from Cloudinary given its secure URL.
        """
        try:
            parts = url.split("/upload/")
            if len(parts) > 1:
                path = parts[1]
                if path.startswith("v") and "/" in path:
                    version_str, rest = path.split("/", 1)
                    if version_str[1:].isdigit():
                        path = rest
                public_id = path.rsplit(".", 1)[0]
                cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Failed to delete image from Cloudinary: {e}")

    def upload_raw_file(self, file_content: bytes, user_id: int, file_id: str) -> str:
        """Upload a raw file (PDF) to Cloudinary and return the secure URL."""
        response = cloudinary.uploader.upload(
            file_content,
            folder="user_cvs",
            public_id=f"user_{user_id}_cv_{file_id}",
            resource_type="raw",
            overwrite=True,
        )
        return response.get("secure_url")

    def delete_raw_file(self, url: str):
        """Delete a raw file from Cloudinary given its secure URL."""
        try:
            parts = url.split("/upload/")
            if len(parts) > 1:
                path = parts[1]
                if path.startswith("v") and "/" in path:
                    version_str, rest = path.split("/", 1)
                    if version_str[1:].isdigit():
                        path = rest
                public_id = path.rsplit(".", 1)[0]
                cloudinary.uploader.destroy(public_id, resource_type="raw")
        except Exception as e:
            print(f"Failed to delete raw file from Cloudinary: {e}")


cloudinary_service = CloudinaryService()
