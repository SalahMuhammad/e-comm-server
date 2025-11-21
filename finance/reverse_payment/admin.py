from django.contrib import admin
from django.utils.html import format_html
# 
from .models import ReversePayment2
from finance.vault_and_methods.services.account_balance_total import get_total_money_in_vaults



@admin.register(ReversePayment2)
class Payment2Admin(admin.ModelAdmin):
    # form = Payment2Form

    list_display = [
        'payment_ref', 
        'date', 
        'owner_name', 
        'amount_display',
        'business_account',
        'status',  
        'status_badge',
        'payment_proof_thumbnail'
    ]
    
    list_filter = ['status', 'business_account', 'date']
    search_fields = ['payment_ref', 'owner__name', 'transaction_id', 'notes']
    date_hierarchy = 'date'
    
    readonly_fields = ['payment_ref', 'created_at', 'created_by', 'last_updated_at', 'last_updated_by']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_ref', 
                ('owner', 'purchase'),
                'amount',
                'business_account',
                'date'
            )
        }),
        ('Payment Details', {
            'fields': (
                ('transaction_id', 'received_by'),
                ('bank_name', 'sender_name'),
                'sender_phone',
                'notes',
                'payment_proof'
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                ('created_at', 'created_by'), 
                ('last_updated_at', 'last_updated_by')
            ),
            'classes': ('collapse',)
        })
    )

    list_per_page = 12
    list_editable = ['status']  # Allow inline status editing

    actions = None  # This removes the actions dropdown
    
    def owner_name(self, obj):
        return obj.owner.name
    owner_name.short_description = 'Supplier'
    
    def amount_display(self, obj):
        formatted_amount = '{:,.2f}'.format(obj.amount)
        return format_html(
            f'<span style="color: green; font-weight: bold;">EGP {formatted_amount}</span>'
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            '1': 'orange',
            '2': 'green',
            '3': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_proof_thumbnail(self, obj):
        if obj.payment_proof:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;"/><a href="{}">path</a>',
                obj.payment_proof.url,
                obj.payment_proof.url
            )
        return '-'
    payment_proof_thumbnail.short_description = 'Proof'
    
    # Custom admin list view CSS
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        # js = ('admin/js/dynamic_sales.js',)

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        obj.last_updated_by = request.user

        super().save_model(request, obj, form, change)
        get_total_money_in_vaults(obj.business_account, True)
