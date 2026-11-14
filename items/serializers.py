from django.db import transaction
from django.forms import ValidationError
from rest_framework import serializers
from items.models import Items, Stock, Barcode, Types, Images,InitialStock, DamagedItems, ItemPriceLog
from common.services.MultySubModelSerializerHandler import WritableMultipleNestedSubmodelsMixin
from items.services.__add_price_log_record import add_price_log_record
from common.services.DynamicFileValidator import DynamicFileValidator
from common.views.CustomQuerysetManager import CustomQuerysetManager



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
		fields = ['id', 'img']


	# def validate_img(self, value):
	# 	if value:
	# 		from common.utilities import comprehensive_image_validation
	# 		comprehensive_image_validation(value)
	# 	return value


# _____________________________________________________________________________________#




class PriceLogSerializer(serializers.ModelSerializer):
	_by_username = serializers.ReadOnlyField(source='by.username')



	class Meta:
		model = ItemPriceLog
		fields = ['price', 'date', 'notes', '_by_username']




# _____________________________________________________________________________________#




class ItemsSerializer(WritableMultipleNestedSubmodelsMixin, serializers.ModelSerializer):
	SUBMODEL_CONFIGS = {
		'barcodes': {'model': Barcode, 'fk': 'item'},
		'images': {'model': Images, 'fk': 'item'}
	}
	FILE_VALIDATOR = DynamicFileValidator({
		"max_size_mb": 5,
		"allowed_mimes": ["image/jpeg", "image/png"],
		"image_rules": {
			"min_width": 30, 
			"min_height": 30
		}
	})



	by_username = serializers.ReadOnlyField(source='by.username')
	images = ImagesSerializer(many=True, required=False)
	stock = StockSerializer(many=True, read_only=True)
	barcodes = BarcodeSerializer(many=True, required=False)
	item_price_log = serializers.SerializerMethodField()
	_type_name = serializers.ReadOnlyField(source='type.name')



	class Meta:
		model = Items
		fields = '__all__'



	def get_item_price_log(self, obj):
		# Pull active logs specifically for this item instance
		manager_name = CustomQuerysetManager().get_manager_name()
		x = getattr(obj.item_price_log.model, manager_name)
		active_logs = x.filter(item=obj)
		return PriceLogSerializer(active_logs, many=True, context=self.context).data


	def validate_barcodes_row(self, row, action):
		err = {}
		barcode = row.get('barcode')
		
		if not barcode:
			err['barcode'] = 'This field is required.'

		exsists_barcode = Barcode.objects.filter(barcode=barcode)
		if exsists_barcode:
			err['barcode'] = f'This barcode already exsists. item: "{exsists_barcode[0].item.name}"'

		if len(barcode) > 49:
			err['barcode'] = f'too long value...'
						
		if err:
			raise serializers.ValidationError(err)

		return row

	def get_barcodes_create_kwargs(self, instance, row):
		return {
			'barcode': row['barcode'],
		}
	
	def get_barcodes_update_kwargs(self, instance, row, sub_obj):
		return {
			'barcode': row['barcode'],
		}

	def validate_images_row(self, row, action):
		err = {}
		img = row.get('_file_obj')

		# 1. Check if the file is missing during create/update
		if (action == 'create' or action == 'update') and not img:
			err['img'] = 'An attachment file is required.'
		elif img:
			try:
				# Read bytes for deep magic-byte & constraint validation
				file_bytes = img.read()
				
				# CRITICAL: Reset the file pointer back to 0 so DRF/Django can save it later
				if hasattr(img, 'seek'):
					img.seek(0)

				is_valid, errors = self.FILE_VALIDATOR.validate_bytes(file_bytes, img.name)
				
				if not is_valid:
					# Pick the first error or join them into a clean string
					err['img'] = errors[0] if errors else "Invalid file."
					
			except Exception as e:
				err['img'] = f"Failed to process file: {str(e)}"

		if err:
			raise serializers.ValidationError(err)

		return row

	def get_images_create_kwargs(self, instance, row):
		kwargs = {}
		
		if row.get('_file_obj'):
			kwargs['img'] = row.get('_file_obj')
			
		return kwargs

	def get_images_update_kwargs(self, instance, row, sub_obj):
		kwargs = {}
		
		if row.get('_file_obj'):
			kwargs['img'] = row.get('_file_obj')

		return kwargs

	@transaction.atomic
	def create(self, validated_data):
		price = validated_data.get('price1', 0)

		res = super().create(validated_data)
		add_price_log_record(price, None, res)

		return res

	@transaction.atomic
	def update(self, instance, validated_data):
		price = validated_data.get('price1', instance.price1)
		old_price = instance.price1

		res = super().update(instance, validated_data)
		add_price_log_record(price, old_price, res)

		return res

	# def __init__(self, *args, **kwargs):
	# 	fieldss = kwargs.pop('fieldss', None)
	# 	super(ItemsSerializer, self).__init__(*args, **kwargs)
	# 	if fieldss:
	# 		allowed = set(fieldss.split(','))
	# 		existing = set(self.fields.keys())
	# 		for field_name in existing - allowed:
	# 			self.fields.pop(field_name)



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




class DamagedItemsSerializer(serializers.ModelSerializer):
	by_username = serializers.ReadOnlyField(source='by.username')
	owner_name = serializers.ReadOnlyField(source='owner.name')
	item_name = serializers.ReadOnlyField(source='item.name')
	repository_name = serializers.ReadOnlyField(source='repository.name')
	

	class Meta:
		model = DamagedItems
		fields = '__all__'
		read_only_fields = ('by', )
