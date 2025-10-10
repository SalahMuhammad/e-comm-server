import json
from rest_framework import serializers
from items.models import Barcode


def http_request_barcodes_handler(item_id, barcodes_data):
	if barcodes_data:
		try:
			barcodes_obj = json.loads(barcodes_data)
			# delete
			barcode_ids = [b['id'] for b in barcodes_obj if b.get('id', None)]
			if barcode_ids:
				Barcode.objects.filter(item_id=item_id).exclude(pk__in=barcode_ids).delete()

			for barcode in barcodes_obj:
				# update exsisting barcode
				if barcode.get('id', None):
					b = Barcode.objects.get(pk=barcode['id'])
					b.barcode = barcode['barcode']
					b.save()
					continue
				# create new barcode
				Barcode.objects.create(
					item_id=item_id,
					barcode=barcode['barcode']
				)
		except Exception as e:
			raise serializers.ValidationError({"detail": f"Error creating/updating barcode: {e}"})
