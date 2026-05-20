from unittest.mock import patch
from app.services.platform.cloudinary_service import cloudinary_service


@patch("app.services.platform.cloudinary_service.cloudinary.uploader.upload")
def test_upload_image(mock_upload):
    mock_upload.return_value = {"secure_url": "https://fake_url.com/image.jpg"}
    url = cloudinary_service.upload_image(b"fake_content", 1)

    mock_upload.assert_called_once_with(
        b"fake_content", folder="profile_pictures", public_id="user_1", overwrite=True
    )
    assert url == "https://fake_url.com/image.jpg"


@patch("app.services.platform.cloudinary_service.cloudinary.uploader.destroy")
def test_delete_image(mock_destroy):
    url = (
        "https://res.cloudinary.com/demo/image/upload/v1234/profile_pictures/user_1.jpg"
    )
    cloudinary_service.delete_image(url)
    mock_destroy.assert_called_once_with("profile_pictures/user_1")


@patch("app.services.platform.cloudinary_service.cloudinary.uploader.destroy")
def test_delete_image_no_version(mock_destroy):
    url = "https://res.cloudinary.com/demo/image/upload/profile_pictures/user_2.png"
    cloudinary_service.delete_image(url)
    mock_destroy.assert_called_once_with("profile_pictures/user_2")
