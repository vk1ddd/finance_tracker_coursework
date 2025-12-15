from django.shortcuts import render, redirect
from .models import Transaction, Account, Category
from django.contrib.auth.decorators import login_required

from django.db.models import Sum
import json

from decimal import Decimal

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    context = {
        'transactions': transactions
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        account_id = request.POST['account']
        category_id = request.POST['category']
        amount = request.POST['amount']
        comment = request.POST['comment']

        account = Account.objects.get(id=account_id)
        category = Category.objects.get(id=category_id)

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            comment=comment
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
        }
        return render(request, 'core/add_transaction.html', context)


@login_required
def dashboard(request):
    expenses = Transaction.objects.filter(user=request.user, category__type='EXPENSE')

    category_expenses = expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')

    category_labels = [item['category__name'] for item in category_expenses]
    category_data = [float(item['total']) for item in category_expenses]

    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')

    context = {
        'transactions': transactions,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
    }
    return render(request, 'core/dashboard.html', context)