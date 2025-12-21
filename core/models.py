from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField(max_length=100, verbose_name="Название счета")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Баланс")

    def __str__(self):
        return self.name

# иконки категорий (удалить)
class CategoryIcon(models.Model):
    name = models.CharField(max_length=50, unique=True)
    svg_code = models.TextField(blank=True, null=True)

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
    icon = models.ForeignKey(CategoryIcon, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name="Название тега")

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Счет")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    timestamp = models.DateField(verbose_name="Дата")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    tags = models.ManyToManyField(Tag, blank=True)

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


class FinancialGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Название цели")
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Целевая сумма")
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Текущая сумма")

    def __str__(self):
        return self.name

class ScheduledTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20)
    next_due_date = models.DateField()

    def __str__(self):
        return self.description


class GoalContribution(models.Model):
    goal = models.ForeignKey(FinancialGoal, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} towards {self.goal.name}"

class Debt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    DEBT_TYPE_CHOICES = [
        ('LEND', 'Я дал в долг'),
        ('BORROW', 'Я взял в долг'),
    ]
    type = models.CharField(max_length=6, choices=DEBT_TYPE_CHOICES, verbose_name="Тип долга")
    person = models.CharField(max_length=100, verbose_name="Кому / У кого")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name="Описание")
    due_date = models.DateField(blank=True, null=True, verbose_name="Дата возврата")
    is_paid = models.BooleanField(default=False, verbose_name="Погашен")

    def __str__(self):
        return f"{self.person} - {self.amount}"

class SavedFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Название фильтра")
    parameters = models.JSONField(verbose_name="Параметры фильтра")

    def __str__(self):
        return self.name