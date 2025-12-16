from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('register/', views.register_view, name='register'),
    path('export/csv/', views.export_transactions_csv, name='export_csv'),
    path('export/xlsx/', views.export_transactions_xlsx, name='export_xlsx'),
]
