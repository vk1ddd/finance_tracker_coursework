from django.shortcuts import render, redirect
from .models import Transaction, Account, Category
from django.contrib.auth.decorators import login_required

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
            account.balance -= float(amount)
        elif category.type == 'INCOME':
            account.balance += float(amount)
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