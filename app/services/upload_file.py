import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service for handling file uploads using Cloudinary.

    This class provides methods to configure Cloudinary and upload files securely.
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initialize the UploadFileService with Cloudinary credentials.

        :param cloud_name: The Cloudinary cloud name.
        :type cloud_name: str

        :param api_key: The Cloudinary API key.
        :type api_key: str

        :param api_secret: The Cloudinary API secret.
        :type api_secret: str

        :raises CloudinaryError:
            If an error occurs during Cloudinary configuration.

        :example:
            >>> upload_service = UploadFileService("my_cloud", "12345", "my_secret")
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username: str) -> str:
        """
        Upload a file to Cloudinary.

        This method uploads the given file to Cloudinary with a predefined
        `public_id` based on the username. The image is stored with a cropped
        resolution of 250x250 pixels.

        :param file: The file object to be uploaded.
        :type file: FileStorage or similar

        :param username: The username used to generate the Cloudinary public ID.
        :type username: str

        :return: The URL of the uploaded image.
        :rtype: str

        :raises CloudinaryError:
            If an error occurs while uploading the file.

        :example:
            >>> uploaded_url = UploadFileService.upload_file(file, "john_doe")
            >>> print(f"File uploaded to: {uploaded_url}")
        """
        public_id = f"ContactPoC/{username}"
        r = cloudinary.uploader.upload(
            file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
