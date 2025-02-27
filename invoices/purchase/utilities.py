from items.models import Items
import json


def update_items_prices(request, status_code):
	condition = request.build_absolute_uri().__contains__('purchase')
	if condition and request.data.get('items', []) and status_code in (200, 201):
		try:
			with open('pp/profitPercentage.json') as profit_percentage:
				pp = json.load(profit_percentage)
			for dict in request.data['items']:
				unit_price = float(dict['unit_price'])
				item = Items.objects.get(pk=dict['item'])
				if not item.price1 == unit_price:
					item.price1 = unit_price
					item.price2 = round(unit_price * float(pp['price2']) + unit_price, 2)
					item.price3 = round(unit_price * float(pp['price3']) + unit_price, 2)
					item.price4 = round(unit_price * float(pp['price4']) + unit_price, 2)
					item.save()
		except Exception as e:
			print(f'an error occurred while updating items prices: {e}')

def compare_items(instance_items, validated_items):
    instance_items_set = set(
        (item.item.id) for item in instance_items) # , item.quantity
    
    validated_items_set = set(
        (validated_item['item'].id) for validated_item in validated_items) # , validated_item.get('quantity', 1)

    # Items to remove and add
    items_to_remove = instance_items_set - validated_items_set
    # items_to_add = validated_items_set - instance_items_set
    # print(items_to_remove)
    # print(items_to_add)
    return items_to_remove#, items_to_add

def compare_items_2(instance_items, validated_items):
    instance_items_set = set(
        (item.item.id) for item in instance_items) # , item.quantity
    
    validated_items_set = set(
        (validated_item['item']) for validated_item in validated_items) # , validated_item.get('quantity', 1)

    # Items to remove and add
    items_to_remove = instance_items_set - validated_items_set
    # items_to_add = validated_items_set - instance_items_set
    # print(items_to_remove)
    # print(items_to_add)
    return items_to_remove if validated_items != [] else []#, items_to_add