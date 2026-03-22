import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional
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
            overwrite=True
        )
        return response.get("secure_url")

    def delete_image(self, url: str):
        """
        Delete an image from Cloudinary given its secure URL.
        """
        # The URL usually looks like: https://res.cloudinary.com/.../image/upload/v1234/profile_pictures/user_1.jpg
        # We need to extract the public ID: "profile_pictures/user_1"
        try:
            # Simple extraction strategy
            parts = url.split("/upload/")
            if len(parts) > 1:
                path = parts[1]
                # Remove version if present e.g. v1235123/
                if path.startswith("v") and "/" in path:
                    version_str, rest = path.split("/", 1)
                    if version_str[1:].isdigit():
                        path = rest

                # Remove extension
                public_id = path.rsplit(".", 1)[0]
                cloudinary.uploader.destroy(public_id)
        except Exception as e:
            # If deletion fails, we log it or pass, so we don't break the flow
            print(f"Failed to delete image from Cloudinary: {e}")

cloudinary_service = CloudinaryService()
