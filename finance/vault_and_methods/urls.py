# urls.py
from django.urls import path
from .views import (
    AccountMovementListView,
    VaultBalanceAPIView,
    ListCreateAccountsView,
    DetailAccountView,
    ListCreateAccountTypeView,
    DetailAccountTypeView
    # VaultBalanceDashboardView,
    # RecalculateVaultBalanceView
    # AccountBalanceHistoryView,
    # MultiAccountSummaryView,
    # AccountMovementExportView
)

# app_name = 'vault_balance'

urlpatterns = [
    # API endpoint for getting balance
    path('balance/', VaultBalanceAPIView.as_view(), name='api_balance'),
    path('account-movements/', AccountMovementListView.as_view(), name='account-movements-list'),


    path('', ListCreateAccountsView.as_view()),
    path('type/', ListCreateAccountTypeView.as_view()),
    path('<str:pk>/', DetailAccountView.as_view()),
    path('type/<str:pk>/', DetailAccountTypeView.as_view()),

    
    # # Dashboard view
    # path('dashboard/', VaultBalanceDashboardView.as_view(), name='dashboard'),
    
    # # Recalculate balance (admin only)
    # path('recalculate/', RecalculateVaultBalanceView.as_view(), name='recalculate'),

    # # Balance history for specific account
    # path(
    #     'account-movements/<int:account_id>/balance-history/',
    #     AccountBalanceHistoryView.as_view(),
    #     name='account-balance-history'
    # ),
    
    # # Multi-account summary
    # path(
    #     'account-movements/multi-summary/',
    #     MultiAccountSummaryView.as_view(),
    #     name='multi-account-summary'
    # ),
    
    # # Export to CSV
    # path(
    #     'account-movements/export/',
    #     AccountMovementExportView.as_view(),
    #     name='account-movements-export'
    # ),
]



"""
API Endpoint Examples:
======================

1. Get all movements (no filters):
   GET /api/account-movements/

2. Get movements for specific account:
   GET /api/account-movements/?account_id=5

3. Get movements for date range (all accounts):
   GET /api/account-movements/?start_date=2025-01-01&end_date=2025-01-31

4. Get movements for account within date range:
   GET /api/account-movements/?account_id=5&start_date=2025-01-01&end_date=2025-01-31

5. Get movements for multiple accounts:
   GET /api/account-movements/?account_ids=5,7,9

6. Include pending transactions:
   GET /api/account-movements/?account_id=5&include_pending=true

7. Get balance history for account:
   GET /api/account-movements/5/balance-history/

8. Get balance history with date range:
   GET /api/account-movements/5/balance-history/?start_date=2025-01-01&end_date=2025-01-31

9. Get multi-account summary:
   GET /api/account-movements/multi-summary/?account_ids=5,7,9

10. Get multi-account summary with date range:
    GET /api/account-movements/multi-summary/?account_ids=5,7,9&start_date=2025-01-01

11. Export movements to CSV:
    GET /api/account-movements/export/?account_id=5&start_date=2025-01-01

Response Examples:
==================

1. AccountMovementListView Response:
{
    "movements": [
        {
            "id": "PAY-123",
            "type": "payment",
            "type_display": "Payment Received",
            "reference": "PAY-20250112-ABC123",
            "date": "2025-01-12T10:30:00Z",
            "account_id": 5,
            "account_name": "Main Cash Register",
            "party": "John Doe",
            "related_doc": "SALE-001",
            "amount_in": "5000.00",
            "amount_out": "0.00",
            "status": "confirmed",
            "notes": "Cash payment"
        },
        {
            "id": "EXP-45",
            "type": "expense",
            "type_display": "Expense",
            "reference": "EXP-45",
            "date": "2025-01-11T14:20:00Z",
            "account_id": 5,
            "account_name": "Main Cash Register",
            "party": "Office Supplies",
            "related_doc": null,
            "amount_in": "0.00",
            "amount_out": "500.00",
            "status": "Approved",
            "notes": "Printer ink"
        }
    ],
    "summary": {
        "total_in": "15000.00",
        "total_out": "3000.00",
        "net_movement": "12000.00",
        "count": 25
    },
    "filters": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "account_id": 5,
        "account_ids": null,
        "include_pending": false
    }
}

2. AccountBalanceHistoryView Response:
{
    "account_id": 5,
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "history": [
        {
            "date": "2025-01-12T10:30:00Z",
            "reference": "PAY-20250112-ABC123",
            "type": "Payment Received",
            "amount_in": "5000.00",
            "amount_out": "0.00",
            "balance_before": "10000.00",
            "balance_after": "15000.00",
            "notes": "Cash payment"
        }
    ],
    "count": 15
}

3. MultiAccountSummaryView Response:
{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "accounts": {
        "5": {
            "account_name": "Main Cash Register",
            "total_in": "15000.00",
            "total_out": "3000.00",
            "net_movement": "12000.00",
            "transaction_count": 25
        },
        "7": {
            "account_name": "Bank Account",
            "total_in": "50000.00",
            "total_out": "25000.00",
            "net_movement": "25000.00",
            "transaction_count": 40
        }
    },
    "total_accounts": 2
}

Error Response Examples:
=========================

1. Invalid date format:
{
    "error": "Invalid parameter: Invalid date format: 2025-13-01. Use YYYY-MM-DD"
}

2. Invalid account_ids:
{
    "error": "Invalid parameter: Invalid integer list: abc,def"
}

3. Both account_id and account_ids specified:
{
    "error": "Cannot specify both account_id and account_ids"
}

4. Missing required parameter:
{
    "error": "account_ids parameter is required"
}
"""
