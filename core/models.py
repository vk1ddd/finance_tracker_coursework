from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField(max_length=100, verbose_name="Название счета")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Баланс")

    def __str__(self):
        return self.name


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=100, verbose_name="Название категории")

    TYPE_CHOICES = [
        ('EXPENSE', 'Расход'),
        ('INCOME', 'Доход'),
    ]
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='EXPENSE', verbose_name="Тип")

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Счет")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    timestamp = models.DateField(verbose_name="Дата")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")

    def __str__(self):
        return f"{self.amount} - {self.category.name}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма лимита")
    month = models.DateField(verbose_name="Месяц бюджета (выберите любой день)")

    def __str__(self):
        month_str = self.month.strftime("%B %Y")
        return f"Лимит для '{self.category.name}' на {month_str}"