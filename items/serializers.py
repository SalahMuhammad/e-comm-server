# from django.db import transaction
from django.forms import ValidationError
from rest_framework import serializers
from items.models import Items, Stock, Barcode, Types, Images,InitialStock


class Base64ImageField(serializers.ImageField):
	"""
	A Django REST framework field for handling image-uploads through raw post data.
	It uses base64 for encoding and decoding the contents of the file.

	Heavily based on
	https://github.com/tomchristie/django-rest-framework/pull/1268

	Updated for Django REST framework 3.
	"""

	def to_internal_value(self, data):
		from django.core.files.base import ContentFile
		import base64
		import six
		import uuid

		if isinstance(data, six.string_types):            
			# Check if the base64 string is in the "data:" format
			if 'data:' in data and ';base64,' in data:
				# Break out the header from the base64 content
				header, data = data.split(';base64,')

			# Try to decode the file. Return validation error if it fails.
			try:
				decoded_file = base64.b64decode(data)
			except TypeError:
				self.fail('invalid_image')

			# Generate file name:
			file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
			# Get the file name extension:
			file_extension = self.get_file_extension(file_name, decoded_file)

			complete_file_name = "%s.%s" % (file_name, file_extension, )

			data = ContentFile(decoded_file, name=complete_file_name)
		return super(Base64ImageField, self).to_internal_value(data)

	def get_file_extension(self, file_name, decoded_file):
		# import imghdr

		# extension = imghdr.what(file_name, decoded_file)
		# extension = "jpg" if extension == "jpeg" else extension
		# return extension
		from PIL import Image
		import io
		
		try:
			with Image.open(io.BytesIO(decoded_file)) as img:
				format_map = {
					'JPEG': 'jpg',
					'PNG': 'png',
					'GIF': 'gif',
					'BMP': 'bmp',
					'WEBP': 'webp'
				}
				return format_map.get(img.format, img.format.lower())
		except Exception:
			raise ValidationError(f"Invalid image file: {file_name}")
	



# _____________________________________________________________________________________#




class StockSerializer(serializers.ModelSerializer):
	repository_name = serializers.ReadOnlyField(source='repository.name')


	class Meta:
		model = Stock
		fields = '__all__'




# _____________________________________________________________________________________#




class BarcodeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Barcode
		fields = ['id', 'barcode']




# _____________________________________________________________________________________#




class ImageURLField(serializers.RelatedField):
    def to_representation(self, value):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(value.img.url)
        # return f'{settings.MEDIA_URL}{value.img}'



class ImagesSerializer(serializers.ModelSerializer):
	# id = serializers.IntegerField(required=False)
	# img = serializers.ImageField(required=False)


	class Meta:
		model = Images
		fields = ['img']


	# def validate_img(self, value):
	# 	if value:
	# 		from common.utilities import comprehensive_image_validation
	# 		comprehensive_image_validation(value)
	# 	return value




# _____________________________________________________________________________________#




class ItemsSerializer(serializers.ModelSerializer):
	by_username = serializers.ReadOnlyField(source='by.username')
	# has_img = serializers.SerializerMethodField()
	# images_upload = serializers.ListField(
	# 		required=False,
	# 		child=Base64ImageField(),
	# 		write_only=True,
	# 	)
	# images_upload = serializers.ListField( 
	# 	required=False,
	# 	child=serializers.ImageField(),
	# 	write_only=True,
	# )
	# images = ImageURLField(many=True, read_only=True)
	images = ImagesSerializer(many=True, read_only=True)
	stock = StockSerializer(many=True, read_only=True)
	barcodes = BarcodeSerializer(many=True, required=False, read_only=True)
	type_name = serializers.ReadOnlyField(source='type.name')


	class Meta:
		model = Items
		fields = '__all__'


	# def __init__(self, *args, **kwargs):
	# 	fieldss = kwargs.pop('fieldss', None)
	# 	super(ItemsSerializer, self).__init__(*args, **kwargs)
	# 	if fieldss:
	# 		allowed = set(fieldss.split(','))
	# 		existing = set(self.fields.keys())
	# 		for field_name in existing - allowed:
	# 			self.fields.pop(field_name)

	# def create(self, validated_data):
	# 	barcodes_data = validated_data.pop('barcodes', None)

	# 	with transaction.atomic():
	# 		item = super().create(validated_data)

	# 		if barcodes_data:
	# 			for barcode in barcodes_data:
	# 				item.barcodes.create(barcode=barcode['barcode'])

	# 		return item

    # def update(self, instance, validated_data):
    #     images_data = validated_data.pop('images', [])
        
    #     with transaction.atomic():
    #         # Update the item instance
    #         instance = super().update(instance, validated_data)

    #         # Handle images
    #         existing_images = {img.id: img for img in instance.images.all()}
            
    #         # Process each image in the request
    #         for image_data in images_data:
    #             image_id = image_data.get('id')
                
    #             if image_id and image_id in existing_images:
    #                 # Update existing image if new file provided
    #                 if 'img' in image_data:
    #                     existing_image = existing_images[image_id]
    #                     existing_image.img = image_data['img']
    #                     existing_image.save()
    #                 existing_images.pop(image_id)
    #             else:
    #                 # Create new image
    #                 if 'img' in image_data:
    #                     Images.objects.create(item=instance, **image_data)

    #         # Delete any remaining old images
    #         for image in existing_images.values():
    #             image.delete()

    #         return instance

	# def get_stock(self, obj):
	# 	return [f'{i.repository}: {i.quantity}, ' for i in obj.stock.all()]

	# def get_by_username(self, obj):
	# 	return obj.by.username
	
	# def get_has_img(self, obj):
	# 	return obj.images.exists()




# _____________________________________________________________________________________#




class TypesSerializer(serializers.ModelSerializer):
	
	
	class Meta:
		model = Types
		fields = '__all__'




# _____________________________________________________________________________________#




class InitialStockSerializer(serializers.ModelSerializer):
	class Meta:
		model = InitialStock
		fields = ['item', 'quantity', "repository", "by"]  # Only allow updating the quantity field




# _____________________________________________________________________________________#




from .models import DamagedItems
class DamagedItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamagedItems
        fields = '__all__'
        read_only_fields = ('by', )
