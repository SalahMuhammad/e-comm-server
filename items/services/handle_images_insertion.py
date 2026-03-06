from common.utilities import comprehensive_image_validation
from items.models import Images


def http_request_images_handler(item_id, images):
	for image_file in images:
		if isinstance(image_file, str):
			continue

		# Skip empty files
		if hasattr(image_file, 'size') and image_file.size == 0:
			continue

		# Skip if not a proper file object
		if not hasattr(image_file, 'read'):
			continue

		if comprehensive_image_validation(image_file):
			Images.objects.create(
				item_id=item_id, 
				img=image_file
			)
