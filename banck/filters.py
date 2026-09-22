from django.db.models import Q
from .models import Account, Card, Transaction, TransactionInside


def own_cards(user):
    return Card.objects.filter(account__user=user)


def own_transactions(user):
    account = Account.objects.filter(user=user).first()
    if not account:
        return Transaction.objects.none()
    return Transaction.objects.filter(Q(sender=account) | Q(reciver=account))


def own_inside_transactions(user):
    account = Account.objects.filter(user=user).first()
    if not account:
        return TransactionInside.objects.none()
    phone = account.user.phone_num
    return TransactionInside.objects.filter(Q(sender=phone) | Q(reciver=phone))
