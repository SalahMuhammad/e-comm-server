# API Endpoints Documentation

## Authentication
- `POST /api/users/register/` - User registration
- `POST /api/users/login/` - User login
- `GET /api/users/user/` - Get current user info
- `POST /api/users/logout/` - User logout

## Items
- `GET /api/items/` - List all items
  - Query params: `limit`, `offset`, `name`, `code`, `type_id`, `repository_id`, `category`
- `POST /api/items/` - Create new item
- `GET /api/items/<int:pk>/` - Get item details
- `PATCH /api/items/<int:pk>/` - Update item
- `DELETE /api/items/<int:pk>/` - Delete item
- `GET /api/items/<int:pk>/fluctuation/` - Get item price fluctuation
  - Query params: `start_date`, `end_date`
- `GET /api/items/quantity-errors-list/` - List quantity errors
  - Query params: `limit`, `offset`, `item_id`, `repository_id`
- `POST /api/items/quantity-errors-corrector/` - Correct quantity errors
- `GET /api/items/types/` - List item types
  - Query params: `limit`, `offset`, `name`
- `POST /api/items/types/` - Create item type
- `GET /api/items/damaged-items/` - List damaged items
  - Query params: `limit`, `offset`, `item_id`, `repository_id`, `start_date`, `end_date`
- `POST /api/items/damaged-items/` - Create damaged item record
- `GET /api/items/damaged-items/<int:pk>/` - Get damaged item details
- `PATCH /api/items/damaged-items/<int:pk>/` - Update damaged item
- `DELETE /api/items/damaged-items/<int:pk>/` - Delete damaged item

## Repositories
- `GET /api/repositories/` - List all repositories
  - Query params: `limit`, `offset`, `name`, `location`
- `POST /api/repositories/` - Create new repository
- `GET /api/repositories/<int:pk>/` - Get repository details
- `PATCH /api/repositories/<int:pk>/` - Update repository
- `DELETE /api/repositories/<int:pk>/` - Delete repository

## Buyer/Supplier Party
- `GET /api/buyer-supplier-party/` - List all parties
  - Query params: `limit`, `offset`, `name`, `phone`, `type`, `city`
- `POST /api/buyer-supplier-party/` - Create new party
- `GET /api/buyer-supplier-party/<int:pk>/` - Get party details
- `PATCH /api/buyer-supplier-party/<int:pk>/` - Update party
- `DELETE /api/buyer-supplier-party/<int:pk>/` - Delete party
- `GET /api/buyer-supplier-party/owner/view/<int:pk>/` - Get owner account view
- `GET /api/buyer-supplier-party/list-of-clients-that-has-credit-balance/` - List clients with credit
  - Query params: `limit`, `offset`, `min_balance`, `max_balance`
- `GET /api/buyer-supplier-party/customer-account-statement/<int:pk>/` - Get customer account statement
  - Query params: `start_date`, `end_date`, `transaction_type`

## Sales Invoices
- `GET /api/sales/` - List all sales invoices
  - Query params: `limit`, `offset`, `no`, `customer_id`, `start_date`, `end_date`, `status`, `note`
- `POST /api/sales/` - Create new sales invoice
- `GET /api/sales/<str:pk>/` - Get sales invoice details
- `PATCH /api/sales/<str:pk>/` - Update sales invoice
- `DELETE /api/sales/<str:pk>/` - Delete sales invoice
- `POST /api/sales/<str:pk>/change-repository-permit/` - Toggle repository permit
- `GET /api/sales/t/sales-refund-totals/` - Get sales and refund totals
  - Query params: `start_date`, `end_date`, `customer_id`
- `GET /api/sales/s/refund/` - List sales return invoices
  - Query params: `limit`, `offset`, `no`, `customer_id`, `start_date`, `end_date`, `status`
- `POST /api/sales/s/refund/` - Create sales return invoice
- `GET /api/sales/s/refund/<str:pk>/` - Get sales return details
- `PATCH /api/sales/s/refund/<str:pk>/` - Update sales return
- `DELETE /api/sales/s/refund/<str:pk>/` - Delete sales return

## Purchase Invoices
- `GET /api/purchases/` - List all purchase invoices
  - Query params: `limit`, `offset`, `no`, `supplier_id`, `start_date`, `end_date`, `status`, `note`
- `POST /api/purchases/` - Create new purchase invoice
- `GET /api/purchases/<str:pk>/` - Get purchase invoice details
- `PATCH /api/purchases/<str:pk>/` - Update purchase invoice
- `DELETE /api/purchases/<str:pk>/` - Delete purchase invoice

## Finance - Payments
- `GET /api/finance/payment/` - List all payments
  - Query params: `limit`, `offset`, `owner_id`, `date`, `start_date`, `end_date`, `status`, `payment_method`, `note`
- `POST /api/finance/payment/` - Create new payment
- `GET /api/finance/payment/<str:pk>/` - Get payment details
- `PATCH /api/finance/payment/<str:pk>/` - Update payment
- `DELETE /api/finance/payment/<str:pk>/` - Delete payment
- `GET /api/finance/payment/?owner_id=<int>&date=<YYYY-MM-DD>&credit_balance=1` - Get owner credit balance

## Finance - Reverse Payments
- `GET /api/finance/reverse-payment/` - List all reverse payments
  - Query params: `limit`, `offset`, `owner_id`, `date`, `start_date`, `end_date`, `status`, `note`
- `POST /api/finance/reverse-payment/` - Create new reverse payment
- `GET /api/finance/reverse-payment/<str:pk>/` - Get reverse payment details
- `PATCH /api/finance/reverse-payment/<str:pk>/` - Update reverse payment
- `DELETE /api/finance/reverse-payment/<str:pk>/` - Delete reverse payment
- `GET /api/finance/reverse-payment/?owner_id=<int>&date=<YYYY-MM-DD>&credit_balance=1` - Get owner credit balance

## Finance - Expenses
- `GET /api/finance/expenses/` - List all expenses
  - Query params: `limit`, `offset`, `category_id`, `start_date`, `end_date`, `status`, `note`, `date_range`
- `POST /api/finance/expenses/` - Create new expense
- `GET /api/finance/expenses/<str:pk>/` - Get expense details
- `PATCH /api/finance/expenses/<str:pk>/` - Update expense
- `DELETE /api/finance/expenses/<str:pk>/` - Delete expense
- `GET /api/finance/expenses/category/list/` - List expense categories
  - Query params: `limit`, `offset`, `name`
- `POST /api/finance/expenses/category/list/` - Create expense category
- `GET /api/finance/expenses/category/<int:pk>/` - Get category details
- `PATCH /api/finance/expenses/category/<int:pk>/` - Update category
- `DELETE /api/finance/expenses/category/<int:pk>/` - Delete category

## Finance - Debt Settlement
- `GET /api/finance/debt-settlement/` - List all debt settlements
  - Query params: `limit`, `offset`, `creditor_id`, `debtor_id`, `start_date`, `end_date`, `status`, `note`
- `POST /api/finance/debt-settlement/` - Create new debt settlement
- `GET /api/finance/debt-settlement/<str:pk>/` - Get debt settlement details
- `PATCH /api/finance/debt-settlement/<str:pk>/` - Update debt settlement
- `DELETE /api/finance/debt-settlement/<str:pk>/` - Delete debt settlement

## Finance - Internal Money Transfer
- `GET /api/finance/internal-money-transfer/` - List all transfers
  - Query params: `limit`, `offset`, `from_account_id`, `to_account_id`, `start_date`, `end_date`, `status`, `note`
- `POST /api/finance/internal-money-transfer/` - Create new transfer
- `GET /api/finance/internal-money-transfer/<str:pk>/` - Get transfer details
- `PATCH /api/finance/internal-money-transfer/<str:pk>/` - Update transfer
- `DELETE /api/finance/internal-money-transfer/<str:pk>/` - Delete transfer

## Finance - Account Vault
- `GET /api/finance/account-vault/balance/` - Get vault balance(s)
  - Query params: `account_id`, `compute_all`
- `GET /api/finance/account-vault/account-movements/` - List account movements
  - Query params: `limit`, `offset`, `start_date`, `end_date`, `account_id`, `account_ids`, `include_pending`, `movement_type`
- `GET /api/finance/account-vault/account-movements/balance-history/` - Get balance history
  - Query params: `account_id`, `start_date`, `end_date`, `limit`, `offset`
- `GET /api/finance/account-vault/account-movements/multi-summary/` - Get multi-account summary
  - Query params: `account_ids` (required), `start_date`, `end_date`
- `GET /api/finance/account-vault/account-movements/export/` - Export movements to CSV
  - Query params: `account_id`, `account_ids`, `start_date`, `end_date`, `include_pending`

## Refillable Items System
- `GET /api/refillable-sys/refunded-items/` - List refunded refillable items
  - Query params: `limit`, `offset`, `item_id`, `owner_id`, `start_date`, `end_date`
- `POST /api/refillable-sys/refunded-items/` - Create refunded item record
- `GET /api/refillable-sys/refunded-items/<int:pk>/` - Get refunded item details
- `PATCH /api/refillable-sys/refunded-items/<int:pk>/` - Update refunded item
- `DELETE /api/refillable-sys/refunded-items/<int:pk>/` - Delete refunded item
- `GET /api/refillable-sys/refilled-items/` - List refilled items
  - Query params: `limit`, `offset`, `item_id`, `owner_id`, `start_date`, `end_date`
- `POST /api/refillable-sys/refilled-items/` - Create refilled item record
- `GET /api/refillable-sys/refilled-items/<int:pk>/` - Get refilled item details
- `PATCH /api/refillable-sys/refilled-items/<int:pk>/` - Update refilled item
- `DELETE /api/refillable-sys/refilled-items/<int:pk>/` - Delete refilled item
- `GET /api/refillable-sys/item-transformer/` - List item transformers
  - Query params: `limit`, `offset`, `source_item_id`, `target_item_id`
- `POST /api/refillable-sys/item-transformer/` - Create item transformer
- `GET /api/refillable-sys/ore-item/` - List ore items
  - Query params: `limit`, `offset`, `name`, `type`
- `POST /api/refillable-sys/ore-item/` - Create ore item
- `GET /api/refillable-sys/ore-item/<int:pk>/` - Get ore item details
- `PATCH /api/refillable-sys/ore-item/<int:pk>/` - Update ore item
- `DELETE /api/refillable-sys/ore-item/<int:pk>/` - Delete ore item
- `GET /api/refillable-sys/refillable-items-owners-has/` - Get owners with refillable items
  - Query params: `limit`, `offset`, `item_id`
- `GET /api/refillable-sys/cans-client-has/<int:pk>/` - Get cans client report
  - Query params: `start_date`, `end_date`

## Employees
- `GET /api/employees/` - List all employees
  - Query params: `limit`, `offset`, `name`, `department`, `status`
- `POST /api/employees/` - Create new employee

## Reports - Warehouse
- `GET /api/reports/item-movement-json/` - Get item movement report (JSON)
  - Query params: `item_id`, `start_date`, `end_date`, `repository_id`, `limit`, `offset`

## Profit/Price Configuration
- `GET /api/pp/` - Get profit percentage configuration
- `POST /api/pp/` - Update profit percentage configuration

## Services
- `GET /api/services/media-browser/` - Browse media files
  - Query params: `path`, `limit`, `offset`
- `GET /api/services/create-db-backup/` - Create database backup
  - Query params: `data_only`
- `GET /api/services/create-items-as-xlsx/` - Export items to XLSX
  - Query params: `repository_id`, `item_type_id`, `category`

## Request Logs
- `GET /api/requests-logs/` - List request logs
  - Query params: `limit`, `offset`, `start_date`, `end_date`, `user_id`, `method`, `status_code`
- `POST /api/requests-logs/` - Create request log (typically auto)
- `GET /api/requests-logs/<int:pk>/` - Get request log details

## Company Information
- `GET /api/company-details/` - Get company details from JSON file

---

## Query Parameters Reference

### Date Filtering
- `start_date` - Format: `YYYY-MM-DD`
- `end_date` - Format: `YYYY-MM-DD`
- `date` - Format: `YYYY-MM-DD`
- `date_range` - Predefined ranges (today, week, month, year)

### Account Filtering
- `account_id` - Single account ID (integer)
- `account_ids` - Multiple account IDs (comma-separated, e.g., `5,7,9`)
- `from_account_id` - Source account for transfers
- `to_account_id` - Destination account for transfers

### Pagination
- `limit` - Number of results per page (default: 12)
- `offset` - Pagination offset

### Common Filters
- `owner` - Filter by owner name (icontains)
- `owner_id` - Filter by owner ID
- `no` - Filter by invoice number (encoded)
- `note` - Filter by notes (icontains)
- `status` - Filter by status
- `name` - Filter by name (icontains)

### Boolean Params
- `compute_all` - Compute all account balances (boolean)
- `include_pending` - Include pending transactions (boolean)
- `data_only` - Backup data only without schema (boolean)