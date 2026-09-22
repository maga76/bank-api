from django.db import models
from django.conf import settings


class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account')
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    passport_id = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.fname} {self.lname} ({self.user.phone_num})"


class Card(models.Model):
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('credit', 'Credit'),
        ('master', 'Master'),
        ('simple', 'Simple'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
    card_id = models.CharField(max_length=16, unique=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    card_name = models.CharField(max_length=10, choices=CARD_TYPES, default='simple')
    cvv = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    expair = models.DateField()

    def __str__(self):
        return self.card_id


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('phone_num', 'Phone Number'),
        ('card', 'Card'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transactions')
    reciver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cuur_balance_sender = models.DecimalField(max_digits=15, decimal_places=2)
    cuur_balance_reciver = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='completed')

    def __str__(self):
        return f"Transaction {self.id}: {self.sender} -> {self.reciver} ({self.amount})"


class TransactionInside(models.Model):
    TYPE_CHOICES = [
        ('phone_num', 'Phone Number'),
        ('card', 'Card'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    sender = models.CharField(max_length=50)
    reciver = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cuur_balance_sender = models.DecimalField(max_digits=15, decimal_places=2)
    cuur_balance_reciver = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='completed')

    def __str__(self):
        return f"Inside {self.id}: {self.sender} -> {self.reciver} ({self.amount})"


class GetCredit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    card_id = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='credits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    procent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Credit {self.id}: {self.card_id} ({self.amount})"


class PutDeposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    card_id = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    procent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Deposit {self.id}: {self.card_id} ({self.amount})"


class BlackListAccount(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='blacklist_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Blacklisted Account: {self.account}"


class BlackListCard(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='blacklist_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Blacklisted Card: {self.card}"
