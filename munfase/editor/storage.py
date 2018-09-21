
#https://stackoverflow.com/questions/9522759/imagefield-overwrite-image-file-with-same-name
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
