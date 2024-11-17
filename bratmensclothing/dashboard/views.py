from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import Users
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from order.models import Order, OrderItem
from django.db.models import Sum, F
from products.models import ProductDetails
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
import json


def is_staff(user):
    return user.is_staff


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def admin_dashboard(request):
    total_users = Users.objects.count()
    total_sales_price = OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('price'))['price__sum'] or 0
    total_order = Order.objects.count()
    total_unit_sold = int(OrderItem.objects.exclude(status='Cancelled').aggregate(Sum('quantity'))['quantity__sum'] or 0)
    total_order_amount = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_discount_amount = Order.objects.annotate(
        total_discount=F('coupon_amount') + F('total_offer_discount')
    ).aggregate(total_discount_amount=Sum('total_discount'))['total_discount_amount'] or 0
    total_canceled_order = OrderItem.objects.filter(status='Cancelled').count()
    total_products_count = ProductDetails.objects.count()
    
    best_selling_products = (
        OrderItem.objects.values(
            "variants__product__product_id",
            "variants__product__product_name",
            "variants__product__image1",
            "variants__product__price",
            "variants__product__occasion",
        )
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:6]
    )

    best_selling_categories = (
        OrderItem.objects
        .values('variants__product__category__category')  
        .annotate(total_sold=Sum('quantity')) 
        .order_by('-total_sold')  
    )

    best_selling_brands = (
        OrderItem.objects.values("variants__product__brand__brandname")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:10]
    )

    # Day-wise Sales Data
    sales_data = Order.objects.annotate(date=TruncDate('created_at')) \
                               .values('date') \
                               .annotate(total_sales=Sum('total_price')) \
                               .order_by('date')
    
    # Week-wise Sales Data
    week_sales_data = Order.objects.annotate(week=TruncWeek('created_at')) \
                                .values('week') \
                                .annotate(total_sales=Sum('total_price')) \
                                .order_by('week')

    # Month-wise Sales Data
    month_sales_data = Order.objects.annotate(month=TruncMonth('created_at')) \
                                    .values('month') \
                                    .annotate(total_sales=Sum('total_price')) \
                                    .order_by('month')

    # year-wise Sales Data
    year_sales_data = Order.objects.annotate(year=TruncYear('created_at')) \
                                .values('year') \
                                .annotate(total_sales=Sum('total_price')) \
                                .order_by('year')
    

    day_labels = [sale['date'].strftime('%Y-%m-%d') for sale in sales_data]  # Date labels for x-axis
    day_data = [float(sale['total_sales']) if sale['total_sales'] is not None else 0.0 for sale in sales_data] 

    # Convert data to labels and sales
    week_labels = [sale['week'].strftime('%Y-%m-%d') for sale in week_sales_data]
    week_data = [float(sale['total_sales']) if sale['total_sales'] is not None else 0.0 for sale in week_sales_data]

    month_labels = [sale['month'].strftime('%Y-%m') for sale in month_sales_data]
    month_data = [float(sale['total_sales']) if sale['total_sales'] is not None else 0.0 for sale in month_sales_data]

    year_labels = [sale['year'].strftime('%Y') for sale in year_sales_data]
    year_data = [float(sale['total_sales']) if sale['total_sales'] is not None else 0.0 for sale in year_sales_data]

    context = {
        'total_users': total_users,
        'total_sales_price': total_sales_price,
        'total_order': total_order,
        'total_unit_sold': total_unit_sold,
        'total_order_amount': total_order_amount,
        'total_discount_amount': total_discount_amount,
        'total_canceled_order': total_canceled_order,
        'total_products_count': total_products_count,
        'day_labels': json.dumps(day_labels),
        'day_data': json.dumps(day_data),
        'week_labels': json.dumps(week_labels),
        'week_data': json.dumps(week_data),
        'month_labels': json.dumps(month_labels),
        'month_data': json.dumps(month_data),
        'year_labels': json.dumps(year_labels),
        'year_data': json.dumps(year_data),
        'best_selling_products':best_selling_products,
        'best_selling_categories':best_selling_categories,
        'best_selling_brands':best_selling_brands      
    }

    return render(request, 'admin/dashboard.html', context)
