"""
    this libs required to run this file
    # Install required package
    pip install reportlab

    # For matplotlib version (optional)
    pip install matplotlib pandas
"""

from datetime import datetime
import os, json

from django.core.management.base import BaseCommand
from invoices.sales.models import SalesInvoice, ReturnInvoice
from refillable_items_system.models import RefundedRefillableItem, RefillableItemsInitialStockClientHas, ItemTransformer
from invoices.buyer_supplier_party.models import Party
from django.db.models import Sum

from itertools import chain



def create_financial_pdf(owner_id):
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_LEFT


    # Create the PDF document
    filename = "financial_report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)

    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Add title
    title = Paragraph("Financial Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Table headers
    headers = ['Date', 'Discount', 'Refund', 'Description', 'Remaining']
    
    # Dummy data for the table
    data = [
        headers,  # Header row
        ['2024-08-15', '$150.00', '$25.00', 'Purchase refund for electronics', '$125.00'],
        ['2024-08-20', '$200.00', '$50.00', 'Service discount applied to account', '$150.00']
    ]
    
    # Create the table
    table = Table(data, colWidths=[1.2*inch, 1*inch, 1*inch, 3*inch, 1*inch])
    
    # Apply table styling
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),
        
        # Alternating row colors for better readability
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#ecf0f1')),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Description column alignment
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
    ]))
    
    # Add the table to elements
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Add footer information
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Build the PDF
    doc.build(elements)
    print(f"PDF generated successfully: {filename}")



class Command(BaseCommand):
    help = 'Generate cans client report'

    def add_arguments(self, parser):
        parser.add_argument('client_id', type=int, help='Client ID')

    def handle(self, *args, **options):
        client_id = options['client_id']

        self.stdout.write(f'Generating report for client {client_id}')

        try:
            file_neame = create_cans_client_has_pdf_matplotlib(client_id)
        except Exception as e: 
            self.stdout.write(e)

        self.stdout.write(
            self.style.SUCCESS(file_neame)
        )


# Alternative version using matplotlib for more chart-like appearance
def create_cans_client_has_pdf_matplotlib(owner_id):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import pandas as pd
    from matplotlib.patches import Rectangle

    
    
    # Create data
    data = get_cans_data_list(owner_id)
    owner_name = Party.objects.get(pk=owner_id).name
    file_name = f'Due DCD Cans Log From {owner_name} - {datetime.now().strftime("%B %d, %Y at %I:%M %p")}.pdf'
    date = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    try:
        os.makedirs(f'media/reports/{owner_name}', exist_ok=True)
        print(f"Directory '{owner_name}' created or already exists.")
    except OSError as e:
        print(f"Error creating directory: {e}")

    df = pd.DataFrame(data)
    num_rows = len(df)
    header_height = .18
    table_row_height = .05
    table_height = (num_rows * table_row_height)
    table_y_position = - (num_rows * table_row_height) + .75 # rest of header_height - due row

    # Create PDF
    with PdfPages(f'media/reports/{owner_name}/{file_name}') as pdf:
        fig, ax = plt.subplots(figsize=(11, 9))
        
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
        # Create header background
        header_rect = Rectangle((0, 0.85), 1, header_height, 
                               facecolor='#2c3e50', edgecolor='none', 
                               transform=ax.transAxes, clip_on=False)
        ax.add_patch(header_rect)
        
        # Add company information to header
        json_file_path = 'media/companyDetails.json'

        with open(json_file_path, 'r') as file:
            company_info = json.load(file)

        # Add company name (larger font)
        ax.text(0.02, 1, company_info['name'], transform=ax.transAxes, 
               fontsize=16, fontweight='bold', color='white', va='top')
        
        ax.text(0.02, 0.95, company_info['description'], transform=ax.transAxes, 
                   fontsize=9, color='white', va='top')
        
        ax.text(0.02, 0.92, company_info['addressDetails'] + company_info['address'], transform=ax.transAxes, 
                   fontsize=7, color='#D3D3D3', va='top')
        
        if hasattr(company_info, 'website'):
            ax.text(0.02, 0.90, company_info['website'], transform=ax.transAxes, 
                    fontsize=7, color='#D3D3D3', va='top')
        
        """
            contact info section
        """
        if 'phone' in company_info['contact']:
            ax.text(0.33, 1, company_info['contact']['phone'], transform=ax.transAxes, 
                    fontsize=7, color='#D3D3D3', va='top')
        
        if 'mobiles' in company_info['contact']:
            for i, info in enumerate(company_info['contact']['mobiles']):
                ax.text(0.33, .975 - (i * 0.025), info, transform=ax.transAxes, 
                    fontsize=7, color='#D3D3D3', va='top')

        if 'emails' in company_info['contact']:
            for i, info in enumerate(company_info['contact']['emails']):
                ax.text(0.48, 1 - (i * 0.025), info, transform=ax.transAxes, 
                    fontsize=7, color='#D3D3D3', va='top')
        
        logo_path = "./media/logo/01.jpeg"
        if os.path.exists(logo_path):
            # Load and display the actual logo
            import matplotlib.image as mpimg
            logo_img = mpimg.imread(logo_path)
            
            # Create an inset axes for the logo
            from mpl_toolkits.axes_grid1.inset_locator import inset_axes
            logo_ax = fig.add_axes([0.78, 0.67, 0.1, 0.08])  # [left, bottom, width, height]
            logo_ax.imshow(logo_img, aspect='equal')
            logo_ax.axis('off')  # Remove axes
        else:
            # Fallback to placeholder if logo file doesn't exist
            logo_rect = Rectangle((0.85, 0.90), 0.1, 0.08, 
                                 facecolor='#666666', edgecolor='white', 
                                 linewidth=1, transform=ax.transAxes, clip_on=False)
            ax.add_patch(logo_rect)
            ax.text(0.9, 0.94, 'Med\nPro Corp', transform=ax.transAxes, 
                   fontsize=8, color='white', ha='center', va='center', fontweight='bold')
        # # Add logo placeholder (you can replace this with actual logo loading)
        # logo_rect = Rectangle((0.85, 0.87), 0.1, 0.08, 
        #                      facecolor='#666666', edgecolor='white', 
        #                      linewidth=1, transform=ax.transAxes, clip_on=False)
        # ax.add_patch(logo_rect)
        # ax.text(0.9, 0.91, 'Med\nPro Corp', transform=ax.transAxes, 
        #        fontsize=8, color='white', ha='center', va='center', fontweight='bold')
        
        # Position the main content lower to accommodate header
        ax.set_position([0.1, 0.1, 0.8, 0.65])
        ax.axis('tight')
        ax.axis('off')

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        # Create table
        table = ax.table(cellText=df.values, colLabels=df.columns,
                        cellLoc='center', loc='center',
                        colWidths=[0.15, 0.15, 0.4, 0.15],
                        bbox=[0, table_y_position, 1, table_height]  # [x, y, width, height] - y=0 gives top margin
                        )
                        # colWidths=[0.15, 0.15, 0.4, 0.15, 0.15])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        # table.scale(1.2, 2)
        table.scale(1, 2)

        # Header styling
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#34495e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Data row styling
        for i in range(1, len(df) + 1):
            for j in range(len(df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#ecf0f1')
                else:
                    table[(i, j)].set_facecolor('#ffffff')
        
        # Current implementation - centered at x=0.5
        ax.text(0.5, 0.8, f'Due DCD Cans Log From "{owner_name}".', 
                transform=ax.transAxes, fontsize=16, fontweight='bold', 
                color='#2c3e50', ha='center', va='center')
        
        # Add timestamp at the bottom of the page - position calculated based on table height
        timestamp_y = table_y_position - 0.05  # Position it slightly below the table
        plt.figtext(0.5, timestamp_y, f"Generated on {date}", 
                   ha='center', fontsize=8, style='italic', color='gray')
        
        pdf.savefig(fig, bbox_inches='tight', dpi=300)
        plt.close()
    
    print("PDF generated successfully: financial_report_matplotlib.pdf")
    return file_name

def create_cans_client_has_pdf_matplotlib_new(owner_id):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import pandas as pd
    from matplotlib.patches import Rectangle
    import json
    import os
    from datetime import datetime
    
    # Create data
    data = get_cans_data_list(owner_id)
    owner_name = Party.objects.get(pk=owner_id).name
    date = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    df = pd.DataFrame(data)
    num_rows = len(df)
    
    # Calculate dynamic figure height based on data
    base_height = 8
    row_height = 0.3  # Height per row
    header_space = 3  # Space for header
    min_height = 11
    
    calculated_height = base_height + (num_rows * row_height) + header_space
    figure_height = max(min_height, calculated_height)
    
    # Create PDF
    with PdfPages(f'Due DCD Cans Log From {owner_name} - {date}.pdf') as pdf:
        fig, ax = plt.subplots(figsize=(11, figure_height))
        
        # Calculate header height ratio based on figure size
        header_height_ratio = 2.5 / figure_height  # Fixed height for header
        header_top = 1 - 0.02  # Small margin from top
        header_bottom = header_top - header_height_ratio
        
        # Create header background with dynamic positioning
        header_rect = Rectangle((0.02, header_bottom), 0.96, header_height_ratio, 
                               facecolor='#2c3e50', edgecolor='none', 
                               transform=ax.transAxes, clip_on=False)
        ax.add_patch(header_rect)
        
        # Load company information
        json_file_path = 'companyDetails.json'
        with open(json_file_path, 'r') as file:
            company_info = json.load(file)

        # Add company information with dynamic positioning
        text_y_start = header_top - 0.02
        text_y_spacing = header_height_ratio / 8  # Divide header space
        
        # Company name (larger font)
        ax.text(0.05, text_y_start, company_info['name'], transform=ax.transAxes, 
               fontsize=16, fontweight='bold', color='white', va='top')
        
        ax.text(0.05, text_y_start - text_y_spacing, company_info['description'], 
               transform=ax.transAxes, fontsize=9, color='white', va='top')
        
        ax.text(0.05, text_y_start - (2 * text_y_spacing), 
               company_info['addressDetails'] + company_info['address'], 
               transform=ax.transAxes, fontsize=7, color='#D3D3D3', va='top')
        
        ax.text(0.05, text_y_start - (3 * text_y_spacing), company_info['website'], 
               transform=ax.transAxes, fontsize=7, color='#D3D3D3', va='top')
        
        # Contact info section
        ax.text(0.35, text_y_start, company_info['contact']['phone'], 
               transform=ax.transAxes, fontsize=7, color='#D3D3D3', va='top')
        
        for i, info in enumerate(company_info['contact']['mobiles']):
            ax.text(0.35, text_y_start - ((i + 1) * text_y_spacing), info, 
                   transform=ax.transAxes, fontsize=7, color='#D3D3D3', va='top')
            
        for i, info in enumerate(company_info['contact']['emails']):
            ax.text(0.50, text_y_start - (i * text_y_spacing), info, 
                   transform=ax.transAxes, fontsize=7, color='#D3D3D3', va='top')
        
        # Logo positioning
        logo_path = "./media/logo/01.jpeg"
        logo_bottom = header_bottom + 0.01
        logo_height = header_height_ratio - 0.02
        
        if os.path.exists(logo_path):
            import matplotlib.image as mpimg
            logo_img = mpimg.imread(logo_path)
            logo_ax = fig.add_axes([0.75, logo_bottom, 0.15, logo_height])
            logo_ax.imshow(logo_img, aspect='equal')
            logo_ax.axis('off')
        else:
            # Fallback placeholder
            logo_rect = Rectangle((0.75, logo_bottom), 0.15, logo_height, 
                                 facecolor='#666666', edgecolor='white', 
                                 linewidth=1, transform=ax.transAxes, clip_on=False)
            ax.add_patch(logo_rect)
            ax.text(0.825, logo_bottom + (logo_height/2), 'Med\nPro Corp', 
                   transform=ax.transAxes, fontsize=8, color='white', 
                   ha='center', va='center', fontweight='bold')
        
        # Calculate content area positioning
        content_top = header_bottom - 0.05  # Space between header and content
        content_height = content_top - 0.1  # Leave space for footer
        
        # Position the main content dynamically
        ax.set_position([0.1, 0.1, 0.8, content_height])
        ax.axis('tight')
        ax.axis('off')

        # Create table with dynamic sizing
        table = ax.table(cellText=df.values, colLabels=df.columns,
                        cellLoc='center', loc='upper center',  # Changed to upper center
                        colWidths=[0.15, 0.15, 0.4, 0.15])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)  # Slightly smaller font for better fit
        
        # Dynamic row height based on content
        if num_rows > 20:
            table.scale(1, 1.5)  # Smaller row height for lots of data
        else:
            table.scale(1, 2)    # Normal row height for less data

        # Header styling
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#34495e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Data row styling
        for i in range(1, len(df) + 1):
            for j in range(len(df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#ecf0f1')
                else:
                    table[(i, j)].set_facecolor('#ffffff')
        
        # Title positioning - dynamically placed between header and table
        title_y_position = content_top + 0.02
        ax.text(0.5, title_y_position, f'Due DCD Cans Log From "{owner_name}".', 
                transform=ax.transAxes, fontsize=16, fontweight='bold', 
                color='#2c3e50', ha='center', va='top')
        
        # Add timestamp at bottom
        plt.figtext(0.5, 0.02, f"Generated on {date}", 
                   ha='center', fontsize=8, style='italic', color='gray')
        
        pdf.savefig(fig, bbox_inches='tight', dpi=300)
        plt.close()
    
    print(f"PDF generated successfully: Due DCD Cans Log From {owner_name} - {date}.pdf")

# if __name__ == "__main__":
#     # Install required packages:
#     # pip install reportlab
#     # pip install matplotlib pandas (for the alternative version)
    
#     try:
#         create_cans_client_has_pdf_matplotlib(sys.argv[1])
#     except ImportError as e:
#         print(f"Missing required package: {e}")
#         print("Please install with: pip install reportlab")


def get_cans_data_list(owner_id):
    data = []

    items = ItemTransformer.objects.all()
    empty = items.values_list('item')
    filled = items.values_list('transform')

    initial_stock_client_has = RefillableItemsInitialStockClientHas.objects.filter(owner_id=owner_id, item_id__in=empty)
    sales_invs = SalesInvoice.objects.filter(owner_id=owner_id, repository_permit=True)
    refund_sales_invs = ReturnInvoice.objects.filter(owner_id=owner_id, repository_permit=True)
    refund = RefundedRefillableItem.objects.filter(owner_id=owner_id)

    result_list = sorted(
        chain(sales_invs, refund_sales_invs, refund, initial_stock_client_has),
        key=get_date,
        # reverse=True,
    )

    remaining = 0
    for instance in result_list:
        if isinstance(instance, SalesInvoice):
            qty = instance.s_invoice_items.filter(item_id__in=filled).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

            if qty == 0: continue

            remaining += qty
            data.append({
                "date": instance.issue_date,
                "qty": qty,
                "description": 'invoice',
                "remaining": remaining
            })
        if isinstance(instance, ReturnInvoice):
            qty = instance.s_invoice_items.filter(item_id__in=filled).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

            if qty == 0: continue

            remaining -= qty
            data.append({
                "date": instance.issue_date,
                "qty": - qty,
                "description": 'invoice refund',
                "remaining": remaining
            })
        elif isinstance(instance, RefundedRefillableItem):
            if instance.quantity == 0: continue

            remaining -= instance.quantity
            data.append({
                "date": instance.date,
                "qty": - instance.quantity,
                "description": 'refund',
                "remaining": remaining
            })
        elif isinstance(instance, RefillableItemsInitialStockClientHas):
            qty = initial_stock_client_has.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
            remaining += qty
            data.append({
                "date": instance.date,
                "qty": qty,
                "description": 'Due from last year',
                "remaining": remaining
            })
    
    return data

def get_date(obj):
    if hasattr(obj, 'date'):
        return obj.date
    elif hasattr(obj, 'issue_date'):
        return obj.issue_date

    return None
