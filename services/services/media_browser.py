import os
from django.conf import settings



def get_media_path_files(path):
    media_root = settings.MEDIA_ROOT
    files = {}

    for root, dirs, filenames in os.walk(media_root):
        if not root.split('/')[-2] == 'media': continue
        
        for filename in filenames:
            # Your custom condition to skip if the parent folder isn't 'media'
            # This assumes a consistent structure like '.../backend/media/subdir'
            # and may need adjustment depending on your exact os.walk behavior 
            # and MEDIA_ROOT setting.
            if 'media' not in root.split('/')[-2:]: # A slightly more robust check
                continue
            
            # Get the name of the current directory (which will be the key)
            dir_name = root.split('/')[-1]

            # Skip the 'media' root itself if it's not meant to hold files
            # Check if we are at the MEDIA_ROOT level itself
            # if dir_name == os.path.basename(media_root.rstrip(os.sep)):
            #     continue
            
            # --- THE FIX IS HERE ---
            # 1. Check if the directory name is a key in the files dictionary
            if dir_name not in files:
                # 2. If it's a new directory, initialize its value as an empty list
                files[dir_name] = []

            # --- END OF FIX ---

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, media_root)
            file_size_bytes = (os.path.getsize(filepath) / 1024).__round__(2)
            files[dir_name].append({'file_name': f'media/{rel_path}', 'size': file_size_bytes})


    return files
