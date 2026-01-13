# API Request Body Examples

This document provides detailed information about what data to send for POST and PATCH requests.

## Quick Reference

- [Items](#items) - Create items, types, damaged items
- [Repositories](#repositories) - Create repositories
- [Buyer/Supplier Party](#buyersupplier-party) - Create customers/suppliers
- [Sales Invoices](#sales-invoices) - Create sales and returns
- [Purchase Invoices](#purchase-invoices) - Create purchases
- [Finance - Payments](#finance---payments) - Record received payments
- [Finance - Reverse Payments](#finance---reverse-payments) - Record outgoing payments
- [Finance - Expenses](#finance---expenses) - Track expenses and categories
- [Finance - Debt Settlement](#finance---debt-settlement) - Settle debts between parties
- [Finance - Internal Money Transfer](#finance---internal-money-transfer) - Transfer between accounts
- [Refillable Items System](#refillable-items-system) - Manage refillable/returnable items
- [Employees](#employees) - Manage employees
- [Authentication](#authentication) - Register and login
- [General Notes](#general-notes) - Important information about field types and formats

---


## Items

### POST /api/items/ - Create Item
```json
{
  "name": "string (required)",
  "code": "string (optional)",
  "type": "integer (required) - Type ID",
  "category": "string (optional)",
  "description": "string (optional)",
  "unit_price": "decimal (required)",
  "by": "integer (required) - User ID"
}
```

### POST /api/items/types/ - Create Item Type
```json
{
  "name": "string (required)"
}
```

### POST /api/items/damaged-items/ - Create Damaged Item
```json
{
  "item": "integer (required) - Item ID",
  "repository": "integer (required) - Repository ID",
  "owner": "integer (optional) - Party ID",
  "quantity": "decimal (required)",
  "date": "string (required) - Format: YYYY-MM-DD",
  "note": "string (optional)"
}
```

---

## Repositories

### POST /api/repositories/ - Create Repository
```json
{
  "name": "string (required)",
  "location": "string (optional)"
}
```

---

## Buyer/Supplier Party

### POST /api/buyer-supplier-party/ - Create Party
```json
{
  "name": "string (required)",
  "phone": "string (optional)",
  "type": "string (required) - Choices: 'customer', 'supplier', 'both'",
  "city": "string (optional)",
  "address": "string (optional)",
  "email": "string (optional)"
}
```

---

## Sales Invoices

### POST /api/sales/ - Create Sales Invoice
```json
{
  "owner": "integer (required) - Customer Party ID",
  "repository_permit": "boolean (optional) - Default: true",
  "notes": "string (optional)",
  "by": "integer (required) - User ID",
  "s_invoice_items": [
    {
      "item": "integer (required) - Item ID",
      "repository": "integer (required) - Repository ID",
      "quantity": "decimal (required)",
      "unit_price": "decimal (required)",
      "discount": "decimal (optional) - Default: 0"
    }
  ]
}
```
**Note**: `total_amount` is auto-calculated from items.

### POST /api/sales/s/refund/ - Create Sales Return Invoice
```json
{
  "owner": "integer (required) - Customer Party ID",
  "original_invoice": "integer (required) - Original Sales Invoice ID",
  "notes": "string (optional)",
  "by": "integer (required) - User ID",
  "s_invoice_items": [
    {
      "item": "integer (required) - Item ID (must exist in original invoice)",
      "repository": "integer (required) - Repository ID",
      "quantity": "decimal (required) - Cannot exceed original quantity",
      "unit_price": "decimal (required)"
    }
  ]
}
```

---

## Purchase Invoices

### POST /api/purchases/ - Create Purchase Invoice
```json
{
  "owner": "integer (required) - Supplier Party ID",
  "repository_permit": "boolean (optional) - Default: true",
  "notes": "string (optional)",
  "by": "integer (required) - User ID",
  "p_invoice_items": [
    {
      "item": "integer (required) - Item ID",
      "repository": "integer (required) - Repository ID",
      "quantity": "decimal (required)",
      "unit_price": "decimal (required)"
    }
  ]
}
```

---

## Finance - Payments

### POST /api/finance/payment/ - Create Payment
```json
{
  "owner": "integer (required) - Payer Party ID",
  "amount": "decimal (required) - Min: 0.01",
  "business_account": "integer (required) - BusinessAccount ID where money was received",
  "sale": "integer (optional) - Related Sales Invoice ID",
  "date": "string (optional) - Format: YYYY-MM-DD, Default: today",
  "status": "string (optional) - Choices: '1' (Pending), '2' (Confirmed), '3' (Rejected), '4' (Reimbursed), Default: '1'",
  "payment_ref": "string (optional) - Auto-generated if not provided",
  "transaction_id": "string (optional) - For InstaPay/Bank Transfer",
  "sender_phone": "string (optional) - For mobile wallets",
  "sender_name": "string (optional) - For bank transfers",
  "bank_name": "string (optional) - For bank transfers",
  "received_by": "string (optional) - Staff member name for cash payments",
  "notes": "string (optional)",
  "payment_proof": "file (optional) - Image upload"
}
```

---

## Finance - Reverse Payments

### POST /api/finance/reverse-payment/ - Create Reverse Payment
```json
{
  "owner": "integer (required) - Payee Party ID",
  "amount": "decimal (required) - Min: 0.01",
  "business_account": "integer (required) - BusinessAccount ID where money was paid from",
  "purchase": "integer (optional) - Related Purchase Invoice ID",
  "date": "string (optional) - Format: YYYY-MM-DD, Default: today",
  "status": "string (optional) - Choices: '1' (Pending), '2' (Confirmed), '3' (Rejected), Default: '1'",
  "payment_ref": "string (optional) - Auto-generated if not provided",
  "transaction_id": "string (optional)",
  "sender_phone": "string (optional)",
  "sender_name": "string (optional)",
  "bank_name": "string (optional)",
  "notes": "string (optional)",
  "payment_proof": "file (optional)"
}
```

---

## Finance - Expenses

### POST /api/finance/expenses/ - Create Expense
```json
{
  "category": "integer (optional) - Expense Category ID",
  "business_account": "integer (required) - BusinessAccount ID",
  "amount": "decimal (required) - Min: 0.01",
  "date": "string (optional) - Format: YYYY-MM-DD, Default: today",
  "status": "string (optional) - Choices: '1' (Pending), '2' (Confirmed), '3' (Rejected), '4' (Reimbursed), Default: '1'",
  "notes": "string (optional) - Max 500 characters",
  "image": "file (optional) - Screenshot or proof upload"
}
```

### POST /api/finance/expenses/category/list/ - Create Expense Category
```json
{
  "name": "string (required) - Max 50 characters, must be unique",
  "description": "string (optional) - Max 200 characters"
}
```


---

## Finance - Debt Settlement

### POST /api/finance/debt-settlement/ - Create Debt Settlement
```json
{
  "owner": "integer (optional) - Party ID",
  "amount": "decimal (required)",
  "date": "string (required) - Format: YYYY-MM-DD",
  "status": "string (optional) - Choices: 'not_approved' (default), 'approved'",
  "note": "string (optional)"
}
```


---

## Finance - Internal Money Transfer

### POST /api/finance/internal-money-transfer/ - Create Transfer
```json
{
  "from_vault": "integer (required) - Source BusinessAccount ID",
  "to_vault": "integer (required) - Destination BusinessAccount ID (must be different from source)",
  "amount": "decimal (required) - Min: 0.01",
  "transfer_type": "string (optional) - Choices: 'internal' (default), 'external', 'p2p'",
  "date": "string (optional) - Format: YYYY-MM-DD, Default: today",
  "notes": "string (optional)",
  "proof": "file (optional) - Image upload"
}
```


---

## Refillable Items System

### POST /api/refillable-sys/refunded-items/ - Create Refunded Item
```json
{
  "item": "integer (required) - Refillable Item ID",
  "owner": "integer (required) - Party ID",
  "repository": "integer (required) - Repository ID",
  "quantity": "decimal (required) - Must be greater than 0",
  "date": "string (required) - Format: YYYY-MM-DD",
  "notes": "string (optional)"
}
```
**Note**: Item must be a refillable item (must exist in ItemTransformer).

### POST /api/refillable-sys/refilled-items/ - Create Refilled Item
```json
{
  "refilled_item": "integer (required) - Refillable Item ID",
  "used_item": "integer (required) - OreItem ID (the raw material used)",
  "employee": "integer (required) - Employee ID",
  "repository": "integer (required) - Repository ID",
  "refilled_quantity": "decimal (required) - Must be greater than 0",
  "used_quantity": "decimal (required) - Must be greater than 0",
  "date": "string (required) - Format: YYYY-MM-DD",
  "notes": "string (optional)"
}
```
**Note**: Refilled item must exist in ItemTransformer.

### POST /api/refillable-sys/item-transformer/ - Create Item Transformer
```json
{
  "item": "integer (required) - Empty/Source Item ID",
  "transform": "integer (required) - Filled/Target Item ID"
}
```
**Note**: Defines transformation relationship (e.g., empty gas cylinder → filled gas cylinder).

### POST /api/refillable-sys/ore-item/ - Create Ore Item
```json
{
  "item": "integer (required) - Item ID (must be unique, one-to-one relationship)"
}
```
**Note**: Ore items represent raw materials used to refill items (e.g., gas, water).


---

## Employees

### POST /api/employees/ - Create Employee
```json
{
  "name": "string (required)",
  "department": "string (optional)",
  "status": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)"
}
```

---

## Authentication

### POST /api/users/register/ - User Registration
```json
{
  "username": "string (required)",
  "email": "string (required)",
  "password": "string (required)",
  "password_confirm": "string (required)"
}
```

### POST /api/users/login/ - User Login
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

---

## General Notes

### Required vs Optional Fields
- **Required fields**: Must be included in the request, or the API will return a 400 Bad Request error
- **Optional fields**: Can be omitted; default values will be used if specified

### Field Types
- **integer**: Whole number (e.g., `5`, `100`)
- **decimal**: Number with decimals (e.g., `10.50`, `99.99`)
- **string**: Text (e.g., `"John Doe"`)
- **boolean**: `true` or `false`
- **file**: Binary file upload (use multipart/form-data)

### Date Format
All date fields use the format: `YYYY-MM-DD` (e.g., `"2025-01-09"`)

### Auto-generated Fields
Some fields are auto-generated if not provided:
- `payment_ref` (for Payments and Reverse Payments) - Format: `PAY-YYYYMMDD-XXXXXXXX` (e.g., `PAY-20250109-A1B2C3D4`)


### Foreign Key References
- When a field requires an ID (e.g., `owner`, `item`, `business_account`), provide the integer ID of the related object
- You can retrieve IDs from the respective GET endpoints

### Nested Objects in Invoices
Sales and Purchase invoices require nested `invoice_items` arrays. Each item in the array represents a line item on the invoice.
