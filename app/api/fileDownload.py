from rest_framework import status, generics, serializers, viewsets, filters, exceptions, permissions, parsers
from app.models import ModelFiles 

class FileDownloadSerializer(serializers.ModelSerializer):
     class Meta:
        model = ModelFiles
        field = ['id', 'name', 'file_name', 'file', 'created_at']


class FileDownload(generics.ListCreateAPIView):
    queryset = ModelFiles.objects.all()
    serailizer_class = FileDownloadSerializer
