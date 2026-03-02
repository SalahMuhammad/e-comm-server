import json
from rest_framework import serializers
from items.models import Barcode


def http_request_barcodes_handler(item_id, barcodes_data, request=None):
	# If the requesting user doesn't have view_barcode permission,
	# skip barcode handling entirely — don't touch existing barcodes.
	if request is not None and not request.user.is_superuser:
		has_view_perm = (
			request.user.has_perm('items.view_barcode')
		)
		if not has_view_perm:
			return

	if barcodes_data:
		try:
			barcodes_obj = json.loads(barcodes_data)
			# delete
			barcode_ids = [b['id'] for b in barcodes_obj if b.get('id', None)]
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
