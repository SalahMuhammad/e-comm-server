from rest_framework import serializers
# from rest_framework.reverse import reverse



class FileItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    extension = serializers.CharField()
    size = serializers.IntegerField()
    modified = serializers.CharField()
    created = serializers.CharField()
    is_file = serializers.BooleanField()
    is_directory = serializers.BooleanField()
    content_type = serializers.CharField()
    permissions = serializers.CharField()


class DirectoryListingSerializer(serializers.Serializer):
    current_path = serializers.CharField()
    parent_path = serializers.CharField(allow_null=True)
    items = FileItemSerializer(many=True)
    total_files = serializers.IntegerField()
    total_directories = serializers.IntegerField()
