from django.contrib import admin
from .models import InitialStock, DamagedItems, ItemPriceLog, Types
from django.contrib.auth.models import Permission

# Register your models here.
admin.site.register(InitialStock)
admin.site.register(DamagedItems)
admin.site.register(ItemPriceLog)
admin.site.register(Types)
admin.site.register(Permission)
