from django.contrib import admin
from .models import OreItem, RefillableItemsInitialStockClientHas, RefundedRefillableItem, ItemTransformer, RefilledItem

# Register your models here.
admin.site.register(OreItem)
admin.site.register(RefillableItemsInitialStockClientHas)
admin.site.register(RefundedRefillableItem)
admin.site.register(ItemTransformer)
admin.site.register(RefilledItem)