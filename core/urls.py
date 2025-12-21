from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('register/', views.register_view, name='register'),
    path('export/csv/', views.export_transactions_csv, name='export_csv'),
    path('export/xlsx/', views.export_transactions_xlsx, name='export_xlsx'),
    path('budgets/', views.manage_budgets, name='budgets'),
    path('transaction/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('filters/save/', views.save_filter, name='save_filter'),
    path('debts/', views.manage_debts, name='manage_debts'),
    path('debts/pay/<int:debt_id>/', views.pay_debt, name='pay_debt'),
]
