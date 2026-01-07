# API Endpoints Documentation

## Authentication
- [`POST /api/users/register/`](finance/vault_and_methods/views.py ) - User registration
- [`POST /api/users/login/`](finance/vault_and_methods/views.py ) - User login
- [`GET /api/users/user/`](finance/payment/views.py ) - Get current user info
- [`POST /api/users/logout/`](finance/vault_and_methods/views.py ) - User logout

## Items
- [`GET /api/items/`](finance/payment/views.py ) - List all items
- [`POST /api/items/`](finance/vault_and_methods/views.py ) - Create new item
- [`GET /api/items/<int:pk>/`](finance/payment/views.py ) - Get item details
- [`PATCH /api/items/<int:pk>/`](items/views.py ) - Update item
- [`DELETE /api/items/<int:pk>/`](items/views.py ) - Delete item
- [`GET /api/items/<int:pk>/fluctuation/`](finance/payment/views.py ) - Get item price fluctuation
- [`GET /api/items/quantity-errors-list/`](finance/payment/views.py ) - List quantity errors
- [`POST /api/items/quantity-errors-corrector/`](finance/vault_and_methods/views.py ) - Correct quantity errors
- [`GET /api/items/types/`](finance/payment/views.py ) - List item types
- [`POST /api/items/types/`](finance/vault_and_methods/views.py ) - Create item type
- [`GET /api/items/damaged-items/`](finance/payment/views.py ) - List damaged items
- [`POST /api/items/damaged-items/`](finance/vault_and_methods/views.py ) - Create damaged item record
- [`GET /api/items/damaged-items/<int:pk>/`](finance/payment/views.py ) - Get damaged item details
- [`PATCH /api/items/damaged-items/<int:pk>/`](items/views.py ) - Update damaged item
- [`DELETE /api/items/damaged-items/<int:pk>/`](items/views.py ) - Delete damaged item

## Repositories
- [`GET /api/repositories/`](finance/payment/views.py ) - List all repositories
- [`POST /api/repositories/`](finance/vault_and_methods/views.py ) - Create new repository
- [`GET /api/repositories/<int:pk>/`](finance/payment/views.py ) - Get repository details
- [`PATCH /api/repositories/<int:pk>/`](items/views.py ) - Update repository
- [`DELETE /api/repositories/<int:pk>/`](items/views.py ) - Delete repository

## Buyer/Supplier Party
- [`GET /api/buyer-supplier-party/`](finance/payment/views.py ) - List all parties
- [`POST /api/buyer-supplier-party/`](finance/vault_and_methods/views.py ) - Create new party
- [`GET /api/buyer-supplier-party/<int:pk>/`](finance/payment/views.py ) - Get party details
- [`PATCH /api/buyer-supplier-party/<int:pk>/`](items/views.py ) - Update party
- [`DELETE /api/buyer-supplier-party/<int:pk>/`](items/views.py ) - Delete party
- [`GET /api/buyer-supplier-party/owner/view/<int:pk>/`](finance/payment/views.py ) - Get owner account view
- [`GET /api/buyer-supplier-party/list-of-clients-that-has-credit-balance/`](finance/payment/views.py ) - List clients with credit
- [`GET /api/buyer-supplier-party/customer-account-statement/<int:pk>/`](finance/payment/views.py ) - Get customer account statement

## Sales Invoices
- [`GET /api/sales/`](finance/payment/views.py ) - List all sales invoices
- [`POST /api/sales/`](finance/vault_and_methods/views.py ) - Create new sales invoice
- [`GET /api/sales/<str:pk>/`](finance/payment/views.py ) - Get sales invoice details
- [`PATCH /api/sales/<str:pk>/`](items/views.py ) - Update sales invoice
- [`DELETE /api/sales/<str:pk>/`](items/views.py ) - Delete sales invoice
- [`POST /api/sales/<str:pk>/change-repository-permit/`](finance/vault_and_methods/views.py ) - Toggle repository permit
- [`GET /api/sales/t/sales-refund-totals/`](finance/payment/views.py ) - Get sales and refund totals
- [`GET /api/sales/s/refund/`](finance/payment/views.py ) - List sales return invoices
- [`POST /api/sales/s/refund/`](finance/vault_and_methods/views.py ) - Create sales return invoice
- [`GET /api/sales/s/refund/<str:pk>/`](finance/payment/views.py ) - Get sales return details
- [`PATCH /api/sales/s/refund/<str:pk>/`](items/views.py ) - Update sales return
- [`DELETE /api/sales/s/refund/<str:pk>/`](items/views.py ) - Delete sales return

## Purchase Invoices
- [`GET /api/purchases/`](finance/payment/views.py ) - List all purchase invoices
- [`POST /api/purchases/`](finance/vault_and_methods/views.py ) - Create new purchase invoice
- [`GET /api/purchases/<str:pk>/`](finance/payment/views.py ) - Get purchase invoice details
- [`PATCH /api/purchases/<str:pk>/`](items/views.py ) - Update purchase invoice
- [`DELETE /api/purchases/<str:pk>/`](items/views.py ) - Delete purchase invoice

## Finance - Payments
- [`GET /api/finance/payment/`](finance/payment/views.py ) - List all payments
- [`POST /api/finance/payment/`](finance/vault_and_methods/views.py ) - Create new payment
- [`GET /api/finance/payment/<str:pk>/`](finance/payment/views.py ) - Get payment details
- [`PATCH /api/finance/payment/<str:pk>/`](items/views.py ) - Update payment
- [`DELETE /api/finance/payment/<str:pk>/`](items/views.py ) - Delete payment
- [`GET /api/finance/payment/?owner-id=<int>&date=<YYYY-MM-DD>&credit-balance=1`](finance/payment/views.py ) - Get owner credit balance

## Finance - Reverse Payments
- [`GET /api/finance/reverse-payment/`](finance/payment/views.py ) - List all reverse payments
- [`POST /api/finance/reverse-payment/`](finance/vault_and_methods/views.py ) - Create new reverse payment
- [`GET /api/finance/reverse-payment/<str:pk>/`](finance/payment/views.py ) - Get reverse payment details
- [`PATCH /api/finance/reverse-payment/<str:pk>/`](items/views.py ) - Update reverse payment
- [`DELETE /api/finance/reverse-payment/<str:pk>/`](items/views.py ) - Delete reverse payment
- [`GET /api/finance/reverse-payment/?owner-id=<int>&date=<YYYY-MM-DD>&credit-balance=1`](finance/payment/views.py ) - Get owner credit balance

## Finance - Expenses
- [`GET /api/finance/expenses/`](finance/payment/views.py ) - List all expenses
- [`POST /api/finance/expenses/`](finance/vault_and_methods/views.py ) - Create new expense
- [`GET /api/finance/expenses/<str:pk>/`](finance/payment/views.py ) - Get expense details
- [`PATCH /api/finance/expenses/<str:pk>/`](items/views.py ) - Update expense
- [`DELETE /api/finance/expenses/<str:pk>/`](items/views.py ) - Delete expense
- [`GET /api/finance/expenses/category/list/`](finance/payment/views.py ) - List expense categories
- [`POST /api/finance/expenses/category/list/`](finance/vault_and_methods/views.py ) - Create expense category
- [`GET /api/finance/expenses/category/<int:pk>/`](finance/payment/views.py ) - Get category details
- [`PATCH /api/finance/expenses/category/<int:pk>/`](items/views.py ) - Update category
- [`DELETE /api/finance/expenses/category/<int:pk>/`](items/views.py ) - Delete category

## Finance - Debt Settlement
- [`GET /api/finance/debt-settlement/`](finance/payment/views.py ) - List all debt settlements
- [`POST /api/finance/debt-settlement/`](finance/vault_and_methods/views.py ) - Create new debt settlement
- [`GET /api/finance/debt-settlement/<str:pk>/`](finance/payment/views.py ) - Get debt settlement details
- [`PATCH /api/finance/debt-settlement/<str:pk>/`](items/views.py ) - Update debt settlement
- [`DELETE /api/finance/debt-settlement/<str:pk>/`](items/views.py ) - Delete debt settlement

## Finance - Internal Money Transfer
- [`GET /api/finance/internal-money-transfer/`](finance/payment/views.py ) - List all transfers
- [`POST /api/finance/internal-money-transfer/`](finance/vault_and_methods/views.py ) - Create new transfer
- [`GET /api/finance/internal-money-transfer/<str:pk>/`](finance/payment/views.py ) - Get transfer details
- [`PATCH /api/finance/internal-money-transfer/<str:pk>/`](items/views.py ) - Update transfer
- [`DELETE /api/finance/internal-money-transfer/<str:pk>/`](items/views.py ) - Delete transfer

## Finance - Account Vault
- [`GET /api/finance/account-vault/balance/`](finance/payment/views.py ) - Get vault balance(s)
  - Query params: [`account_id`](finance/vault_and_methods/services/AccountMovementService.py ), [`compute_all`](finance/vault_and_methods/views.py )
- [`GET /api/finance/account-vault/account-movements/`](finance/payment/views.py ) - List account movements
  - Query params: [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`end_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`account_id`](finance/vault_and_methods/services/AccountMovementService.py ), [`account_ids`](finance/vault_and_methods/services/AccountMovementService.py ), [`include_pending`](finance/vault_and_methods/services/AccountMovementService.py )
- [`GET /api/finance/account-vault/account-movements/balance-history/`](finance/payment/views.py ) - Get balance history
  - Query params: [`account_id`](finance/vault_and_methods/services/AccountMovementService.py ), [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`end_date`](finance/vault_and_methods/services/AccountMovementService.py )
- [`GET /api/finance/account-vault/account-movements/multi-summary/`](finance/payment/views.py ) - Get multi-account summary
  - Query params: [`account_ids`](finance/vault_and_methods/services/AccountMovementService.py ) (required), [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`end_date`](finance/vault_and_methods/services/AccountMovementService.py )
- [`GET /api/finance/account-vault/account-movements/export/`](finance/payment/views.py ) - Export movements to CSV
  - Query params: [`account_id`](finance/vault_and_methods/services/AccountMovementService.py ), [`account_ids`](finance/vault_and_methods/services/AccountMovementService.py ), [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`end_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`include_pending`](finance/vault_and_methods/services/AccountMovementService.py )

## Refillable Items System
- [`GET /api/refillable-sys/refunded-items/`](finance/payment/views.py ) - List refunded refillable items
- [`POST /api/refillable-sys/refunded-items/`](finance/vault_and_methods/views.py ) - Create refunded item record
- [`GET /api/refillable-sys/refunded-items/<int:pk>/`](finance/payment/views.py ) - Get refunded item details
- [`PATCH /api/refillable-sys/refunded-items/<int:pk>/`](items/views.py ) - Update refunded item
- [`DELETE /api/refillable-sys/refunded-items/<int:pk>/`](items/views.py ) - Delete refunded item
- [`GET /api/refillable-sys/refilled-items/`](finance/payment/views.py ) - List refilled items
- [`POST /api/refillable-sys/refilled-items/`](finance/vault_and_methods/views.py ) - Create refilled item record
- [`GET /api/refillable-sys/refilled-items/<int:pk>/`](finance/payment/views.py ) - Get refilled item details
- [`PATCH /api/refillable-sys/refilled-items/<int:pk>/`](items/views.py ) - Update refilled item
- [`DELETE /api/refillable-sys/refilled-items/<int:pk>/`](items/views.py ) - Delete refilled item
- [`GET /api/refillable-sys/item-transformer/`](finance/payment/views.py ) - List item transformers
- [`POST /api/refillable-sys/item-transformer/`](finance/vault_and_methods/views.py ) - Create item transformer
- [`GET /api/refillable-sys/ore-item/`](finance/payment/views.py ) - List ore items
- [`POST /api/refillable-sys/ore-item/`](finance/vault_and_methods/views.py ) - Create ore item
- [`GET /api/refillable-sys/ore-item/<int:pk>/`](finance/payment/views.py ) - Get ore item details
- [`PATCH /api/refillable-sys/ore-item/<int:pk>/`](items/views.py ) - Update ore item
- [`DELETE /api/refillable-sys/ore-item/<int:pk>/`](items/views.py ) - Delete ore item
- [`GET /api/refillable-sys/refillable-items-owners-has/`](finance/payment/views.py ) - Get owners with refillable items
- [`GET /api/refillable-sys/cans-client-has/<int:pk>/`](finance/payment/views.py ) - Get cans client report

## Employees
- [`GET /api/employees/`](finance/payment/views.py ) - List all employees
- [`POST /api/employees/`](finance/vault_and_methods/views.py ) - Create new employee

## Reports - Warehouse
- [`GET /api/reports/item-movement-json/`](finance/payment/views.py ) - Get item movement report (JSON)
  - Query params: [`item_id`](reports/warehouse/views.py ), [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`end_date`](finance/vault_and_methods/services/AccountMovementService.py ), [`repository_id`](reports/warehouse/services/item_movement_service.py )

## Profit/Price Configuration
- [`GET /api/pp/`](finance/payment/views.py ) - Get profit percentage configuration
- [`POST /api/pp/`](finance/vault_and_methods/views.py ) - Update profit percentage configuration

## Services
- [`GET /api/services/media-browser/`](finance/payment/views.py ) - Browse media files
- [`GET /api/services/create-db-backup/`](finance/payment/views.py ) - Create database backup
  - Query params: [`data-only`](env/lib/python3.10/site-packages/rest_framework/serializers.py )
- [`GET /api/services/create-items-as-xlsx/`](finance/payment/views.py ) - Export items to XLSX

## Request Logs
- [`GET /api/requests-logs/`](finance/payment/views.py ) - List request logs
- [`POST /api/requests-logs/`](finance/vault_and_methods/views.py ) - Create request log (typically auto)
- [`GET /api/requests-logs/<int:pk>/`](finance/payment/views.py ) - Get request log details

## Company Information
- [`GET /api/company-details/`](finance/payment/views.py ) - Get company details from JSON file

---

## Query Parameters Reference

### Date Filtering
- [`start_date`](finance/vault_and_methods/services/AccountMovementService.py ) - Format: `YYYY-MM-DD`
- [`end_date`](finance/vault_and_methods/services/AccountMovementService.py ) - Format: `YYYY-MM-DD`

### Account Filtering
- [`account_id`](finance/vault_and_methods/services/AccountMovementService.py ) - Single account ID (integer)
- [`account_ids`](finance/vault_and_methods/services/AccountMovementService.py ) - Multiple account IDs (comma-separated, e.g., `5,7,9`)

### Pagination
- `limit` - Number of results per page (default: 12)
- `offset` - Pagination offset

### Common Filters
- [`owner`](common/views.py ) - Filter by owner name (icontains)
- `no` - Filter by invoice number (encoded)
- [`note`](common/views.py ) - Filter by notes (icontains)
- [`status`](env/lib/python3.10/site-packages/rest_framework/response.py ) - Filter by status
- [`date_range`](finance/expenses/services/filters.py ) - Date range filter for expenses