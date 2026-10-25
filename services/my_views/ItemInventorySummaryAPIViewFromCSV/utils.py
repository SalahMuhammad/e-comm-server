import os
import csv
from django.conf import settings

def get_safe_item_name(item_name: str) -> str:
    """Matches your exact sanitization logic."""
    return "".join(c for c in item_name if c.isalnum() or c in (" ", "_", "-")).strip()

def parse_detailed_csv(file_path):
    """Parses multi-section and multi-subsection detailed item CSVs into clean structured JSON."""
    if not os.path.exists(file_path):
        return None

    sections = {}
    current_section = "summary_overview"
    section_rows = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if not row:
                continue
            
            joined_row_str = "".join(row).strip()
            
            # Check for main section headers (e.g., "=== 6. REFILLABLE ITEM DETAILS ===")
            if joined_row_str.startswith("===") and joined_row_str.endswith("==="):
                if section_rows:
                    sections[current_section] = section_rows
                    section_rows = []
                current_section = joined_row_str.strip("= ").lower().replace(" ", "_")
                continue
            
            # Check for subsection headers (e.g., "-- Refilled & Used Items Transactions --")
            if joined_row_str.startswith("--") and joined_row_str.endswith("--"):
                if section_rows:
                    sections[current_section] = section_rows
                    section_rows = []
                current_section = joined_row_str.strip("- ").lower().replace(" ", "_")
                continue
            
            section_rows.append(row)
        
        if section_rows:
            sections[current_section] = section_rows

    # Format sections into clean JSON structures
    structured_data = {}
    
    # 1. Summary Overview
    summary_dict = {}
    for row in sections.get("item_summary_overview", []):
        if len(row) >= 2:
            summary_dict[row[0].strip()] = row[1].strip()
    structured_data["summary_overview"] = summary_dict

    # 2. Tabular and subsection handling
    for key, raw_rows in sections.items():
        if key == "item_summary_overview":
            continue
            
        if raw_rows:
            # Check if first row is a header (contains column names)
            header = raw_rows[0]
            rows = []
            for row in raw_rows[1:]:
                if len(row) == 1 and "No " in row[0]:
                    rows.append({"message": row[0]})
                    break
                if len(row) == len(header):
                    rows.append(dict(zip(header, row)))
                else:
                    rows.append({"raw": ",".join(row)})
            structured_data[key] = rows

    return structured_data