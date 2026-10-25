import os
import csv
from decimal import Decimal
from common.encoder import MixedRadixEncoder


def export_item_detailed_csvs(items_data, output_dir="media/year-closure/inventory_detailed_exports"):
    """
    Creates individual CSV files for each item, structured with clear sections 
    showing every underlying transaction leading up to the totals.
    """
    os.makedirs(output_dir, exist_ok=True)

    for item_data in items_data:
        item_name = item_data["item_name"]
        safe_item_name = "".join(c for c in item_name if c.isalnum() or c in (" ", "_", "-")).strip()
        file_path = os.path.join(output_dir, f"{safe_item_name}.csv")

        with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)

            # --- HEADER / OVERVIEW ---
            writer.writerow(["=== ITEM SUMMARY OVERVIEW ==="])
            writer.writerow(["Item Name", item_name])
            writer.writerow(["Total Initial Stock Qty", item_data.get("initail_stock_qty", 0)])
            writer.writerow(["Total Purchased Qty", item_data.get("purchased_qty", 0)])
            writer.writerow(["Total Sold Refund Qty", item_data.get("sold_refund", 0)])
            writer.writerow(["Total Sold Qty", item_data.get("sold_qty", 0)])
            writer.writerow(["Total Damaged Qty", item_data.get("damaged_total", 0)])

            writer.writerow(["Refillable items data"])
            writer.writerow(["Total Refillable Refunded", item_data.get("refillable_item_details", {}).get("refund", 0)])
            writer.writerow(["Total Refillable Refilled", item_data.get("refillable_item_details", {}).get("refilled", 0)])
            writer.writerow(["Total Refillable Used Qty", item_data.get("refillable_item_used", 0)])

            writer.writerow([])

            writer.writerow(["Total Item Profit", item_data.get("item_profits", 0)])

            writer.writerow([])

            # --- SECTION 0: PRICE LOG ---
            writer.writerow(["=== 0. PRICE LOG TRANSACTIONS ==="])
            writer.writerow(["price", "Date", "Notes"])
            price_log = item_data.get("price_log_records", [])
            if price_log:
                for row in price_log:
                    writer.writerow([row["price"], row["date"], row["notes"]])
            else:
                writer.writerow(["No PRICE LOG Records", ""])
            writer.writerow([])

            # --- SECTION 1: INITIAL STOCK ---
            writer.writerow(["=== 1. INITIAL STOCK TRANSACTIONS ==="])
            writer.writerow(["Repository", "Quantity", "Date", "Notes"])
            initial_stocks = item_data.get("initial_stock_records", [])
            if initial_stocks:
                for row in initial_stocks:
                    writer.writerow([row["repository"], row["quantity"], row["date"], row["notes"]])
            else:
                writer.writerow(["No Initial Stock Records", ""])
            writer.writerow([])

            # --- SECTION 2: PURCHASE INVOICES ---
            writer.writerow(["=== 2. PURCHASE INVOICE TRANSACTIONS ==="])
            writer.writerow(["id", "Invoice Date", "Repository Permit", "Repository", "Quantity", "Unit Price", "Discount", "Tax Rate", "Invoice Note", "Item desc"])
            purchases = item_data.get("purchase_records", [])
            if purchases:
                for row in purchases:
                    writer.writerow([
                        MixedRadixEncoder().encode(row["id"]), row["issue_date"], row["repository_permit"], row["repository"],
                        row["quantity"], row["unit_price"], row["discount"], row["tax_rate"], row["invoice_note"], row['desc']
                    ])
            else:
                writer.writerow(["No Purchase Transactions", "", "", "", "", "", ""])
            writer.writerow([])

            # --- SECTION 3: SALES INVOICES & PROFIT BREAKDOWN ---
            writer.writerow(["=== 3. SALES INVOICE TRANSACTIONS & PROFITS ==="])
            writer.writerow(["id", "Invoice Date", "Repository Permit", "Repository", "Quantity", "Selling Price", "Matched Cost (PriceLog)", "Refund Profit", "Line Profit", "Invoice Note", "Item desc"])
            sales = item_data.get("sales_records", [])
            if sales:
                for row in sales:
                    writer.writerow([
                        MixedRadixEncoder().encode(int(row["id"])), row["issue_date"], row["repository_permit"], row["repository"],
                        row["quantity"], row["unit_price"], row["cost_price"], row["refund_profit"], row["line_profit"] - row["refund_profit"], row["invoice_note"], row['desc']
                    ])
            else:
                writer.writerow(["No Sales Transactions", "", "", "", "", "", ""])
            writer.writerow([])

            # --- SECTION 4: RETURN / REFUND INVOICES ---
            writer.writerow(["=== 4. RETURN INVOICE TRANSACTIONS ==="])
            writer.writerow(["id", "Invoice Date", "Repository Permit", "Repository", "Quantity", "Unit Price", "Invoice Note", "Item desc"])
            returns = item_data.get("return_records", [])
            if returns:
                for row in returns:
                    writer.writerow([
                        MixedRadixEncoder().encode(row["id"]), row["issue_date"], row["repository_permit"], row["repository"],
                        row["quantity"], row["unit_price"], row["invoice_note"], row['desc']
                    ])
            else:
                writer.writerow(["No Return Transactions", "", "", "", ""])
            writer.writerow([])

            # --- SECTION 5: DAMAGED ITEMS ---
            writer.writerow(["=== 5. DAMAGED ITEMS ==="])
            writer.writerow(["Repository", "Quantity", "Date", "Notes"])
            damaged = item_data.get("damaged_records", [])
            if damaged:
                for row in damaged:
                    writer.writerow([row["repository"], row["quantity"], row["date"], row["notes"]])
            else:
                writer.writerow(["No Damaged Items", ""])
            writer.writerow([])

            # --- SECTION 6: REFILLABLE ITEM TRANSACTIONS ---
            writer.writerow(["=== 6. REFILLABLE ITEM DETAILS ==="])
            writer.writerow(["-- Refunded Refillable Items (Client Returns) --"])
            writer.writerow(["Repository", "Quantity", "Date", "Notes"])
            refill_refunds = item_data.get("refillable_refund_records", [])
            if refill_refunds:
                for row in refill_refunds:
                    writer.writerow([row["repository"], row["quantity"], row["date"], row["notes"]])
            else:
                writer.writerow(["No Refillable Refunds", ""])

            writer.writerow([])

            writer.writerow(["-- Refilled & Used Items Transactions --"])
            writer.writerow(["Repository", "Refilled Quantity", "Used Item", "Used Quantity", "Date", "Notes"])
            refill_ops = item_data.get("refillable_ops_records", [])
            if refill_ops:
                for row in refill_ops:
                    writer.writerow([row["repository"], row["refilled_quantity"], row["used_item"], row["used_quantity"], row["date"], row["notes"]])
            else:
                writer.writerow(["No Refilled/Used Operations", "", ""])
            writer.writerow([])

            # --- SECTION 7: REMAINING BY REPOSITORY ---
            # writer.writerow(["=== 7. REMAINING STOCK BY REPOSITORY ==="])
            # writer.writerow(["Repository Name", "Remaining Balance Qty"])
            # repos = item_data.get("remaing_in_repositroies", [])
            # if repos:
            #     for repo in repos:
            #         writer.writerow([repo["repo_name"], repo["qty"]])
            # else:
            #     writer.writerow(["No Stock Remaining", 0])

    print(f"Detailed section-based CSVs generated in: {output_dir}")

