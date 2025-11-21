from django.contrib import admin
from .models import AccountType, BusinessAccount

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_by', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('get_by', 'get_updated_by', 'created_at', 'updated_at')
    list_per_page = 25

    def get_by(self, obj):
        return obj.by.username if obj.by else '-'
    get_by.short_description = 'Created By'

    def get_updated_by(self, obj):
        return obj.updated_by.username if obj.updated_by else '-'
    get_updated_by.short_description = 'Updated By'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(BusinessAccount)
class BusinessAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_type', 'current_balance', 'is_active')
    list_filter = ('account_type', 'is_active', 'bank_name')
    search_fields = ('account_name', 'account_number', 'phone_number', 'bank_name')
    readonly_fields = ('get_by', 'get_updated_by', 'created_at', 'updated_at')
    fieldsets = (
        ('Account Information', {
            'fields': ('account_type', 'account_name', 'is_active')
        }),
        ('Account Details', {
            'fields': ('account_number', 'phone_number', 'bank_name')
        }),
        ('Balance Information', {
            'fields': ('current_balance',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('get_by', 'get_updated_by', 'created_at', 'updated_at')
        }),
    )
    list_per_page = 25

    def get_by(self, obj):
        return obj.by.username if obj.by else '-'
    get_by.short_description = 'Created By'

    def get_updated_by(self, obj):
        return obj.updated_by.username if obj.updated_by else '-'
    get_updated_by.short_description = 'Updated By'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
