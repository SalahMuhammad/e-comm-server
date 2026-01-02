from rest_framework.pagination import PageNumberPagination
from items.models import Stock
from decimal import Decimal, ROUND_HALF_UP


def set_request_items_totals(items):
	total_amount = 0
	for i, item in enumerate(items):
		quantity = item.get('quantity', 1)
		unit_price = item['unit_price'] 
		tax_rate = item.get('tax_rate', 0)
		discount = item.get('discount', 0)

		item['quantity'] = Decimal(str(quantity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['unit_price'] = Decimal(str(unit_price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['tax_rate'] = Decimal(str(tax_rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		item['discount'] = Decimal(str(discount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		
		item['total'] = Decimal(str((item['quantity'] * item['unit_price']) + item['tax_rate'] - item['discount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

		total_amount += item['total']

	return items, total_amount


def insert_invoice_items(invoice_instance, items_relations_name, items):
	"""
	Insert invoice items and adjust stock accordingly.

	This function creates invoice items for a given invoice instance and adjusts
	the stock levels based on the items' quantities.

	Args:
		invoice_instance: The invoice object to which items will be added.
		items_relations_name (str): The name of the relation for invoice items.
		items (list): A list of dictionaries containing item data.
		adjust_stock_sign (int, optional): Multiplier for stock adjustment. 
			Use -1 for reducing stock (e.g., sales), 1 for increasing (e.g., purchases). 
			Defaults to 1.

	Returns:
		None

	Side effects:
		- Creates new invoice items linked to the invoice_instance.
		- Adjusts stock levels for each item in the Stock model.
	"""
	# Todo: Add validation for items
	for item_data in items:
		getattr(invoice_instance, items_relations_name).create(
			repository_id=item_data['repository'],
			item_id=item_data['item'],
			description=item_data.get('description', ''),
			quantity=item_data.get('quantity', 1),
			unit_price=item_data.get('unit_price', 0),
			tax_rate=item_data.get('tax_rate', 0),
			discount=item_data.get('discount', 0),
			total=item_data.get('total', 0)
		)

def adjust_stock(items, adjust_stock_sign):
	for item in items:
		stock, cretated = Stock.objects.get_or_create(
			repository=item.repository,
			item=item.item
		)
		stock.adjust_stock(item.quantity * adjust_stock_sign)

def get_pagination_class(self):
        if self.request.query_params.get('full_report') == 'true':            
            class CustomPagination(PageNumberPagination):
                page_size = 10000
                
            return CustomPagination
        return self.pagination_class


import hashlib
def short_hash_number(num):
	# Use a short hash: take the integer value of the md5 digest and encode in base36 for compactness
	return hashlib.md5(str(num).encode()).hexdigest()[:8]  # first 8 chars



from PIL import Image
import imghdr
from rest_framework.serializers import ValidationError


def comprehensive_image_validation(file, max_size_mb=5):
    """
    Comprehensive image validation
    """
    # Check file size
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError({'detail': f'File size exceeds {max_size_mb}MB limit'})
    
    # Check MIME type
    allowed_mime_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if hasattr(file, 'content_type') and file.content_type not in allowed_mime_types:
        raise ValidationError({'detail': 'Invalid file type. Only JPEG, JPG, PNG, GIF, and WebP are allowed.'})
    
    # Check file signature
    file.seek(0)
    image_type = imghdr.what(file)
    if image_type not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
        raise ValidationError({'detail': 'File is not a valid image.'})
    
    # Use PIL to validate and check image properties
    try:
        file.seek(0)
        with Image.open(file) as img:
            img.verify()  # Verify it's a complete image
            
            # Additional checks
            file.seek(0)
            with Image.open(file) as img:
                width, height = img.size
                
                # Check dimensions if needed
                if width > 4000 or height > 4000:
                    raise ValidationError({'detail': 'Image dimensions too large (max 4000x4000)'})
                
                if width < 50 or height < 50:
                    raise ValidationError({'detail': 'Image dimensions too small (min 50x50)'})
    
    except (IOError, SyntaxError) as e:
        raise ValidationError({'detail': 'Invalid image file'})
    
    finally:
        file.seek(0)  # Reset file pointer
    
    return True
