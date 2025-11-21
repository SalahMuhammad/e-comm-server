from django.contrib import admin

# Register your models here.
from django.contrib import admin

from finance.vault_and_methods.services.account_balance_total import get_total_money_in_vaults
from .models import MoneyTransfer



@admin.register(MoneyTransfer)
class TransferAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'last_updated_at', 'last_updated_by')    
    list_display = ('from_vault', 'to_vault', 'amount', 'date', 'transfer_type')
    list_filter = ('from_vault', 'to_vault', 'date')
    search_fields = ('from_vault__account_name', 'to_vault__account_name')
    date_hierarchy = 'date'
    list_per_page = 20

    actions = None  # This removes the actions dropdown

    fieldsets = (
        ('Basic Information', {
            'fields': ('from_vault', 'to_vault', 'amount', 'date')
        }),
        ('Notes', {
            'fields': ('notes', 'proof')
        }),
        ('System Information', {
            'fields': ('created_at', 'created_by', 'last_updated_at', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New instance
            obj.created_by = request.user
        obj.last_updated_by = request.user

        super().save_model(request, obj, form, change)
        get_total_money_in_vaults(obj.from_vault, True)
        get_total_money_in_vaults(obj.to_vault, True)
