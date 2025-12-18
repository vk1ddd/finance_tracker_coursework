from django.shortcuts import render, redirect
from .models import Transaction, Account, Category
from django.contrib.auth.decorators import login_required

from django.db.models import Sum
import json

from decimal import Decimal

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

import csv
import openpyxl
from django.http import HttpResponse

from datetime import date

from datetime import date, timedelta


@login_required
def dashboard(request):
    today = date.today()

    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)

    year, month = int(year), int(month)

    selected_month_start = date(year, month, 1)

    transactions_this_month = Transaction.objects.filter(
        user=request.user,
        timestamp__year=year,
        timestamp__month=month
    )

    income_this_month = transactions_this_month.filter(category__type='INCOME').aggregate(Sum('amount'))[
                            'amount__sum'] or Decimal('0.00')
    expenses_this_month = transactions_this_month.filter(category__type='EXPENSE').aggregate(Sum('amount'))[
                              'amount__sum'] or Decimal('0.00')
    savings_this_month = income_this_month - expenses_this_month

    total_balance = Account.objects.filter(user=request.user).aggregate(Sum('balance'))['balance__sum'] or 0.00

    category_expenses = transactions_this_month.filter(category__type='EXPENSE').values('category__name').annotate(
        total=Sum('amount')).order_by('-total')

    category_labels = [item['category__name'] for item in category_expenses]
    category_data = [float(item['total']) for item in category_expenses]

    prev_month_date = selected_month_start - timedelta(days=1)
    prev_month = {
        'year': prev_month_date.year,
        'month': prev_month_date.month
    }

    next_month_date = (selected_month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    next_month = {
        'year': next_month_date.year,
        'month': next_month_date.month
    }

    context = {
        'transactions': transactions_this_month.order_by('-timestamp'),
        'total_balance': total_balance,
        'income_this_month': income_this_month,
        'expenses_this_month': expenses_this_month,
        'savings_this_month': savings_this_month,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'current_month': selected_month_start,
        'prev_month': prev_month,
        'next_month': next_month,
    }

    return render(request, 'core/dashboard.html', context)


def add_transaction(request):
    if request.method == 'POST':
        account_id = request.POST['account']
        category_id = request.POST['category']
        amount = request.POST['amount']
        comment = request.POST['comment']

        transaction_date_str = request.POST['transaction_date']
        if transaction_date_str:
            transaction_date = transaction_date_str
        else:
            transaction_date = date.today()

        account = Account.objects.get(id=account_id, user=request.user)
        category = Category.objects.get(id=category_id, user=request.user)

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            comment=comment,
            timestamp=transaction_date
        )

        if category.type == 'EXPENSE':
            account.balance -= Decimal(amount)
        elif category.type == 'INCOME':
            account.balance += Decimal(amount)
        account.save()

        return redirect('dashboard')

    else:
        accounts = Account.objects.filter(user=request.user)
        categories = Category.objects.filter(user=request.user)
        context = {
            'accounts': accounts,
            'categories': categories,
            'today': date.today().strftime('%Y-%m-%d'),
        }
        return render(request, 'core/add_transaction.html', context)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Сохраняем нового пользователя
            login(request, user)  # Сразу авторизуем его
            return redirect('dashboard')  # И перенаправляем на дашборд
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'registration/register.html', context)





@login_required
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Дата', 'Счет', 'Категория', 'Тип', 'Сумма', 'Комментарий'])

    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    for t in transactions:
        writer.writerow(
            [t.timestamp.strftime('%d.%m.%Y %H:%M'), t.account.name, t.category.name, t.category.get_type_display(),
             t.amount, t.comment])

    return response


@login_required
def export_transactions_xlsx(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Транзакции'

    headers = ['Дата', 'Счет', 'Категория', 'Тип', 'Сумма', 'Комментарий']
    worksheet.append(headers)

    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    for t in transactions:
        worksheet.append(
            [t.timestamp.strftime('%d.%m.%Y %H:%M'), t.account.name, t.category.name, t.category.get_type_display(),
             t.amount, t.comment])

    workbook.save(response)
    return response
