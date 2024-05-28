from dotenv import load_dotenv
load_dotenv()

import cloudinary
from cloudinary import CloudinaryImage
import cloudinary.uploader

from django.core.files.uploadedfile import InMemoryUploadedFile

config = cloudinary.config(secure=True)

def uploadImage(file: InMemoryUploadedFile):
    try:
        response = cloudinary.uploader.upload(file, folder='visnet')
        print(response['secure_url'])
         
        return response['secure_url']

    except Exception as e:
        print(f"an error occured while uploading image to cloudinary")
        raise e
        

