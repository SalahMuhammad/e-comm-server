from django.contrib import admin
from .models import InitialStock, DamagedItems, ItemPriceLog, Types
from django.contrib.auth.models import Permission

# Register your models here.
admin.site.register(InitialStock)
admin.site.register(DamagedItems)
admin.site.register(ItemPriceLog)
# admin.site.register(Types)
admin.site.register(Permission)



from django.contrib import admin
from .models import Items, Images, Barcode


class ImagesInline(admin.TabularInline):
    model = Images
    extra = 1
    fields = ('img', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.img:
            return f'<img src="{obj.img.url}" style="max-height: 100px; max-width: 100px;" />'
        return "No image"
    image_preview.short_description = 'Preview'
    image_preview.allow_tags = True


class BarcodeInline(admin.TabularInline):
    model = Barcode
    extra = 1
    fields = ('barcode',)


@admin.register(Types)
class TypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'by')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'by')
    
    fieldsets = (
        ('Type Information', {
            'fields': ('name', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Items)
class ItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'price1', 'price2', 'price3', 'price4', 
                    'is_refillable', 'origin', 'place', 'created_at')
    list_filter = ('type', 'is_refillable', 'created_at', 'updated_at')
    search_fields = ('name', 'origin', 'place', 'barcodes__barcode')
    readonly_fields = ('created_at', 'updated_at', 'by')
    inlines = [ImagesInline, BarcodeInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'is_refillable')
        }),
        ('Pricing', {
            'fields': ('price1', 'price2', 'price3', 'price4')
        }),
        ('Location Details', {
            'fields': ('origin', 'place')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.by = request.user

        super().save_model(request, obj, form, change)


# @admin.register(Images)
# class ImagesAdmin(admin.ModelAdmin):
#     list_display = ('id', 'item', 'image_preview', 'img')
#     list_filter = ('item',)
#     search_fields = ('item__name',)
#     readonly_fields = ('image_preview',)
    
#     def image_preview(self, obj):
#         if obj.img:
#             return f'<img src="{obj.img.url}" style="max-height: 150px; max-width: 150px;" />'
#         return "No image"
#     image_preview.short_description = 'Preview'
#     image_preview.allow_tags = True
    
#     def delete_model(self, request, obj):
#         """Override to ensure file deletion when deleting from admin"""
#         if obj.img:
#             if os.path.isfile(obj.img.path):
#                 os.remove(obj.img.path)
#         super().delete_model(request, obj)
    
#     def delete_queryset(self, request, queryset):
#         """Override to ensure file deletion when bulk deleting from admin"""
#         for obj in queryset:
#             if obj.img:
#                 if os.path.isfile(obj.img.path):
#                     os.remove(obj.img.path)
#         super().delete_queryset(request, queryset)


# @admin.register(Barcode)
# class BarcodeAdmin(admin.ModelAdmin):
#     list_display = ('barcode', 'item')
#     list_filter = ('item',)
#     search_fields = ('barcode', 'item__name')
    
#     fieldsets = (
#         (None, {
#             'fields': ('item', 'barcode')
#         }),
#     )
