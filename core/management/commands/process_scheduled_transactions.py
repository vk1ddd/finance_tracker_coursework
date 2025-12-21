from django.core.management.base import BaseCommand
from datetime import date
from dateutil.relativedelta import relativedelta
from core.models import ScheduledTransaction, Transaction, Account


class Command(BaseCommand):
    help = 'Обрабатывает регулярные транзакции, у которых наступил срок.'

    def handle(self, *args, **options):
        today = date.today()
        due_transactions = ScheduledTransaction.objects.filter(next_due_date__lte=today)

        if not due_transactions.exists():
            self.stdout.write(self.style.SUCCESS('Нет регулярных платежей для обработки сегодня.'))
            return

        for st in due_transactions:
            self.stdout.write(f'Обработка: {st.description}')

            Transaction.objects.create(
                user=st.user,
                account=st.account,
                category=st.category,
                amount=st.amount,
                comment=f"Автоплатеж: {st.description}",
                timestamp=today
            )

            st.account.balance -= st.amount
            st.account.save()

            if st.frequency == 'monthly':
                st.next_due_date += relativedelta(months=1)
            elif st.frequency == 'yearly':
                st.next_due_date += relativedelta(years=1)
            st.save()

            self.stdout.write(self.style.SUCCESS(f'Транзакция создана. Следующая дата: {st.next_due_date}'))