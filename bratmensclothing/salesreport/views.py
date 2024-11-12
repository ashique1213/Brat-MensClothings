from django.shortcuts import render,redirect
from products.models import ProductDetails
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from products.models import ProductDetails
from order.models import Order,OrderItem
from coupon.models import Coupon
from offer.models import Brand_Offers,Product_Offers
from django.db.models import Sum, Count,F
from django.db.models.functions import TruncDate
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from io import BytesIO
import openpyxl
from django.http import HttpResponse
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_salesreport(request):
    total_sales_price = OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('price'))['price__sum'] or 0
    total_order=Order.objects.count()
    total_unit_sold=int(OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('quantity'))['quantity__sum'] or 0)
    total_order_amount=Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_discount_amount = Order.objects.annotate(
            total_discount=F('coupon_amount') + F('total_offer_discount')
        ).aggregate(total_discount_amount=Sum('total_discount'))['total_discount_amount'] or 0

    sales_report = Order.objects.annotate(date=TruncDate('created_at')) \
    .values('date') \
    .annotate(
        total_sales_revenue=Sum('total_price'),
        coupon_applied=Sum('coupon_amount'),
        offer_applied=Sum('total_offer_discount'),                                                                                                                                   
        net_sales=Sum('total_price') -Sum(F('coupon_amount')+F('total_offer_discount')), 
        number_of_orders=Count('order_id'),
        total_items_sold=Sum('items__quantity', default=0)  
    ) \
    .order_by('date')
    context={
        'total_sales_price':total_sales_price,
        'total_order':total_order,
        'total_unit_sold':total_unit_sold,
        'total_order_amount':total_order_amount,
        'total_discount_amount':total_discount_amount,
        'sales_report':sales_report,
    }
    
    return render(request,'admin/salesreport.html',context)



@never_cache
def download_pdf(request):
    response = FileResponse(generate_pdf_file(), as_attachment=True, filename='sales_report.pdf')
    return response


def generate_pdf_file():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontSize=12, leading=14, alignment=1)  # Center align
    info_style = ParagraphStyle(name='InfoStyle', fontSize=10, leading=12, alignment=1)    # Center align

    # Add company information
    elements.append(Paragraph("B.R.A.T Mens Clothings PVT.", title_style))
    elements.append(Paragraph("Email: bratmensclothings@gmail.com", info_style))
    elements.append(Paragraph("Website: bratclothings.com", info_style))
    elements.append(Spacer(1, 12))  # Space between header and title

    # Add Sales Report title
    elements.append(Paragraph("Sales Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # Calculate summary data
    total_sales_price = OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('price'))['price__sum'] or 0
    total_order = Order.objects.count()
    total_unit_sold = int(OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('quantity'))['quantity__sum'] or 0)
    total_order_amount = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_discount_amount = Order.objects.annotate(
        total_discount=F('coupon_amount') + F('total_offer_discount')
    ).aggregate(total_discount_amount=Sum('total_discount'))['total_discount_amount'] or 0

    # Add summary data to PDF
    summary_data = [
        ["Total Sales Price:", f"{total_sales_price:.2f}"],
        ["Total Orders:", total_order],
        ["Total Units Sold:", total_unit_sold],
        ["Total Order Amount:", f"{total_order_amount:.2f}"],
        ["Total Discount Amount:", f"{total_discount_amount:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 8),      
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),    
        ('LEFTPADDING', (0, 0), (-1, 0), 5),      
        ('RIGHTPADDING', (0, 0), (-1, 0), 5), 
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 12))  # space between summary and sales report table

    # Fetch sales report data
    sales_report = Order.objects.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(
            total_sales_revenue=Sum('total_price'),
            coupon_applied=Sum('coupon_amount'),
            offer_applied=Sum('total_offer_discount'),
            net_sales=Sum('total_price') - Sum(F('coupon_amount') + F('total_offer_discount')),
            number_of_orders=Count('order_id'),
            total_items_sold=Sum('items__quantity', default=0)
        ) \
        .order_by('date')

    # Prepare table data for sales report
    data = [
        ["Date", "Total Sales Revenue", "Coupon Applied", "Offer Applied", "Net Sales", "Number of Orders", "Total Items Sold"]
    ]

    for report in sales_report:
        data.append([
            report['date'].strftime("%Y-%m-%d"),
            f"{report['total_sales_revenue']:.2f}",
            f"{report['coupon_applied']:.2f}",
            f"{report['offer_applied']:.2f}",
            f"{report['net_sales']:.2f}",
            report['number_of_orders'],
            int(report['total_items_sold'])
        ])

    # Create and style the sales report table
    table = Table(data, colWidths=[1 * inch, 1.2 * inch, 1 * inch, 1 * inch, 1 * inch, 1* inch, 1 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),      
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),   
        ('LEFTPADDING', (0, 0), (-1, 0), 5),      
        ('RIGHTPADDING', (0, 0), (-1, 0), 5), 
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer



def download_to_excel(request):
    # Create a new workbook and a sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"
    
    # Prepare header row
    headers = [
        "Date", "Total Sales Revenue", "Coupon Applied", "Offer Applied", 
        "Net Sales", "Number of Orders", "Total Items Sold"
    ]
    
    # Apply bold font style to the headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
    
    ws.append(headers)

    # Get the sales report data
    sales_report = Order.objects.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(
            total_sales_revenue=Sum('total_price'),
            coupon_applied=Sum('coupon_amount'),
            offer_applied=Sum('total_offer_discount'),
            net_sales=Sum('total_price') - Sum(F('coupon_amount') + F('total_offer_discount')),
            number_of_orders=Count('order_id'),
            total_items_sold=Sum('items__quantity', default=0)
        ) \
        .order_by('date')

    # Loop through the sales report and add data rows to the Excel sheet
    for report in sales_report:
        row = [
            report['date'].strftime("%Y-%m-%d"),
            f"₹{int(report['total_sales_revenue']) if report['total_sales_revenue'] else 0}",
            f"₹{int(report['coupon_applied']) if report['coupon_applied'] else 0}",
            f"₹{int(report['offer_applied']) if report['offer_applied'] else 0}",
            f"₹{int(report['net_sales']) if report['net_sales'] else 0}",
            int(report['number_of_orders']),
            int(report['total_items_sold']),
        ]
        ws.append(row)

    # Adjust column widths dynamically based on the content length
    for col_num in range(1, len(headers) + 1):
        max_length = 0
        column = get_column_letter(col_num)
        for row in ws.iter_rows(min_col=col_num, max_col=col_num):
            for cell in row:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
        adjusted_width = (max_length + 2)  # Add a little padding
        ws.column_dimensions[column].width = adjusted_width

    # Prepare the response to download the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'
    wb.save(response)  # Save the workbook to the response buffer

    return response
