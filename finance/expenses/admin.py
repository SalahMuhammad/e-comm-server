from django.contrib import admin

from finance.vault_and_methods.services.account_balance_total import get_total_money_in_vaults
from .models import Category, Expense

class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'last_updated_at', 'last_updated_by')

    def save_model(self, request, obj, form, change):
        if not change:  # New instance
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ('name', 'description', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 20

class ImagesInline(admin.TabularInline):
    # model = Images
    extra = 1
    readonly_fields = ('created_at', 'created_by', 'last_updated_at', 'last_updated_by')
    
    # def save_model(self, request, obj, form, change):
    #     if not change:
    #         obj.created_by = request.user
    #     obj.last_updated_by = request.user
    #     super().save_model(request, obj, form, change)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['created_by', 'last_updated_by']:
            kwargs['initial'] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.pk:  # New instance
                obj.created_by = request.user
            obj.last_updated_by = request.user
            obj.save()

        # Handle deleted instances
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

@admin.register(Expense)
class ExpenseAdmin(BaseModelAdmin):
    # list_display = ('category', 'business_account', 'amount', 'date', 'status', 'created_by')
    list_display = ('category', 'business_account', 'amount', 'date', 'status', 'image', 'created_by')
    list_filter = ('status', 'date', 'category', 'business_account')
    search_fields = ('notes', 'category__name', 'business_account__account_name')
    date_hierarchy = 'date'
    list_per_page = 20
    # inlines = [ImagesInline]

    list_editable = ['status']  # Allow inline status editing
    actions = None  # This removes the actions dropdown
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'business_account', 'amount', 'date')
        }),
        ('Status & Notes', {
            # 'fields': ('status', 'notes')
            'fields': ('status', 'notes', 'image')
        }),
        ('System Information', {
            'fields': ('created_at', 'created_by', 'last_updated_at', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    # def save_formset(self, request, form, formset, change):
    #     instances = formset.save(commit=False)
    #     for obj in instances:
    #         if not obj.pk:  # New instance
    #             obj.created_by = request.user
    #         obj.last_updated_by = request.user
    #         obj.save()

    #     # Handle deleted instances
    #     for obj in formset.deleted_objects:
    #         obj.delete()

    #     formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        obj.last_updated_by = request.user

        super().save_model(request, obj, form, change)
        get_total_money_in_vaults(obj.business_account, True)

# @admin.register(Images)
# class ImagesAdmin(BaseModelAdmin):
#     list_display = ('expense', 'image', 'created_by', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('expense__notes',)
#     list_per_page = 20
