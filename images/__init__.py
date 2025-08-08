import os

SUPPORTED_FORMATS = ['.png', '.ico']
AVAILABLE_IMAGES = {}

this_dir, this_file = os.path.split((os.path.abspath(__file__)))

# NOTE - StevenPince - This package will Automatically detect images placed in this folder.
#                      Other parts of the application can access it by importing "get_image"
#
#                      from image import get_image
#                      get_image('favicon')

for image_file in os.listdir(this_dir):
    if image_file != this_file:
        image_name, ext = os.path.splitext(image_file)
        if ext in SUPPORTED_FORMATS:
            AVAILABLE_IMAGES[image_name] = os.path.join(this_dir, image_file)


def get_image(requested_image_name: str) -> str:
    return AVAILABLE_IMAGES.get(requested_image_name, '')


FAVICON = get_image('favicon')
