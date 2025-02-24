import os
from django.core.management.base import BaseCommand
from .models import Images
from django.conf import settings

class Command(BaseCommand):
    help = 'Deletes images from the filesystem and database where item is null'

    def handle(self, *args, **kwargs):
        for img in Images.objects.filter(item__isnull=True):
            # Delete from filesystem
            img_path = os.path.join(settings.MEDIA_ROOT, str(img.file_field_name))
            if os.path.exists(img_path):
                os.remove(img_path)
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {img_path} from filesystem'))
            else:
                self.stdout.write(self.style.WARNING(f'{img_path} does not exist on filesystem'))
            
            # Delete from database
            img.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted image with ID {img.id} from database'))


def delete_unused_imagesss():
    for img in Images.objects.filter(item__isnull=True):
        # Delete from filesystem
        img_path = os.path.join(settings.MEDIA_ROOT, str(img.file_field_name))  # Replace 'file_field_name' with the actual field name
        if os.path.exists(img_path):
            os.remove(img_path)
            print(f'Successfully deleted {img_path} from filesystem')
        else:
            print(f'{img_path} does not exist on filesystem')
        
        # Delete from database
        img_id = img.id  # Store the ID for logging purposes
        img.delete()
        print(f'Successfully deleted image with ID {img_id} from database')

# Call the function
# delete_unused_images()