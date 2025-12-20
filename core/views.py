from django.shortcuts import render, redirect
from .models import Transaction, Account, Category, Budget, Tag
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

from django.shortcuts import render, redirect, get_object_or_404


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

    if savings_this_month < 0:
        savings_this_month = 0

    total_balance = Account.objects.filter(user=request.user).aggregate(Sum('balance'))['balance__sum'] or 0.00

    category_expenses = transactions_this_month.filter(category__type='EXPENSE').values('category__name').annotate(
        total=Sum('amount')).order_by('-total')

    category_labels = [item['category__name'] for item in category_expenses]
    category_data = [float(item['total']) for item in category_expenses]

    budgets = Budget.objects.filter(user=request.user, month__year=year, month__month=month)
    expenses_map = {item['category__name']: item['total'] for item in category_expenses}

    budget_progress_list = []
    for budget in budgets:
        spent = expenses_map.get(budget.category.name, 0)
        percent = int((spent / budget.amount) * 100) if budget.amount > 0 else 0
        budget_progress_list.append({
            'category_name': budget.category.name,
            'limit': budget.amount,
            'spent': spent,
            'percent': percent,
        })

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
        'transactions': transactions_this_month.order_by('-timestamp', '-id'),
        'total_balance': total_balance,
        'income_this_month': income_this_month,
        'expenses_this_month': expenses_this_month,
        'savings_this_month': savings_this_month,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'current_month': selected_month_start,
        'prev_month': prev_month,
        'next_month': next_month,
        'budget_progress_list': budget_progress_list,
    }

    return render(request, 'core/dashboard.html', context)


def add_transaction(request):
    if request.method == 'POST':
        account_id = request.POST['account']
        category_id = request.POST['category']
        amount = request.POST['amount']
        comment = request.POST['comment']
        transaction_date_str = request.POST['transaction_date']

        tags_string = request.POST.get('tags', '')

        if transaction_date_str:
            transaction_date = transaction_date_str
        else:
            transaction_date = date.today()

        account = get_object_or_404(Account, id=account_id, user=request.user)
        category = get_object_or_404(Category, id=category_id, user=request.user)

        new_transaction = Transaction(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            comment=comment,
            timestamp=transaction_date
        )
        new_transaction.save()

        if tags_string:
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(user=request.user, name=name)
                new_transaction.tags.add(tag)

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


@login_required
def manage_budgets(request):
    today = date.today()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    year, month = int(year), int(month)
    selected_month_start = date(year, month, 1)

    if request.method == 'POST':
        category_ids = request.POST.getlist('category_id')
        for category_id in category_ids:
            limit_amount = request.POST.get(f'limit_{category_id}')
            category = Category.objects.get(id=category_id, user=request.user)

            if limit_amount and Decimal(limit_amount) > 0:
                Budget.objects.update_or_create(
                    user=request.user,
                    category=category,
                    month=selected_month_start,
                    defaults={'amount': limit_amount}
                )
            else:
                Budget.objects.filter(user=request.user, category=category, month=selected_month_start).delete()

        return redirect(f"{request.path}?year={year}&month={month}")

    expense_categories = Category.objects.filter(user=request.user, type='EXPENSE')
    existing_budgets = Budget.objects.filter(user=request.user, month__year=year, month__month=month)
    budgets_map = {b.category.id: b.amount for b in existing_budgets}

    categories_with_budgets = []
    for category in expense_categories:
        categories_with_budgets.append({
            'category': category,
            'limit': budgets_map.get(category.id)
        })

    prev_month_date = selected_month_start - timedelta(days=1)
    prev_month = {'year': prev_month_date.year, 'month': prev_month_date.month}
    next_month_date = (selected_month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    next_month = {'year': next_month_date.year, 'month': next_month_date.month}

    context = {
        'categories_with_budgets': categories_with_budgets,
        'current_month': selected_month_start,
        'prev_month': prev_month,
        'next_month': next_month,
    }
    return render(request, 'core/budgets.html', context)


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        account = transaction.account

        if transaction.category.type == 'EXPENSE':
            account.balance += transaction.amount
        elif transaction.category.type == 'INCOME':
            account.balance -= transaction.amount
        account.save()

        transaction.delete()

    return redirect('dashboard')