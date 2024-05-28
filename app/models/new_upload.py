from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _, gettext
from django.utils import timezone
import os

def user_directory_path(instance, filename):
    filename = os.path.basename(filename)
    return os.path.join('3d_models', str(instance.owner.id), filename) 

class ModelFiles(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, help_text=_("The user who uploaded a model"), verbose_name=_("Owner") )
    name = models.CharField(max_length=255, help_text=_("Name of the model"), verbose_name=_("Name"))
    file_name = models.CharField(max_length=255, help_text=_("Name of the file"), verbose_name=_("File name"))
    file_url = models.URLField(max_length=255, help_text=_("Cloudinary url of the file"), verbose_name=_("File url"), blank=True)
    page_url = models.URLField(max_length=255, help_text=_("Page url for the model"), verbose_name=_("Page url"), blank=True)
    created_at = models.DateTimeField(default=timezone.now, help_text=_("Creation date"), verbose_name=_("Created at"))

    def __str__(self):
        self.name
