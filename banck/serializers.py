import secrets
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from accounts.models import User
from .models import *


def _move_account_balance(sender, receiver, amount):
    if not Account.objects.filter(pk=sender.pk, balance__gte=amount).update(
        balance=F('balance') - amount
    ):
        raise serializers.ValidationError('Not enough money')
    Account.objects.filter(pk=receiver.pk).update(balance=F('balance') + amount)
    sender.refresh_from_db(fields=['balance'])
    receiver.refresh_from_db(fields=['balance'])


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'fname', 'lname', 'passport_id', 'balance']


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'card_id', 'card_name', 'balance', 'created_at', 'expair']
        read_only_fields = ['id', 'card_id', 'balance', 'created_at']

    def create(self, data):
        user = self.context['request'].user
        account = Account.objects.filter(user=user).first()

        if not account:
            raise serializers.ValidationError('Account not found')

        while True:
            card_id = str(1000000000000000 + secrets.randbelow(9000000000000000))
            if not Card.objects.filter(card_id=card_id).exists():
                break

        return Card.objects.create(
            account=account,
            card_id=card_id,
            card_name=data.get('card_name', 'simple'),
            cvv=str(100 + secrets.randbelow(900)),
            expair=data.get('expair')
        )


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'sender', 'reciver', 'amount',
            'cuur_balance_sender', 'cuur_balance_reciver',
            'description', 'status', 'created_at'
        ]


class TransactionInsideSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionInside
        fields = [
            'id', 'type', 'sender', 'reciver', 'amount',
            'cuur_balance_sender', 'cuur_balance_reciver',
            'description', 'status', 'created_at'
        ]


class GetCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = GetCredit
        fields = ['id', 'card_id', 'amount', 'procent', 'status', 'created_at']


class PutDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = PutDeposit
        fields = ['id', 'card_id', 'amount', 'procent', 'status', 'created_at']


class BlackListAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackListAccount
        fields = ['id', 'account', 'created_at', 'description']


class BlackListCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackListCard
        fields = ['id', 'card', 'created_at', 'description']


class TransferByCardSerializer(serializers.Serializer):
    receiver_card_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False)

    def create(self, data):
        sender = Account.objects.filter(user=self.context['request'].user).first()

        card = Card.objects.filter(card_id=data['receiver_card_id']).first()

        if not sender:
            raise serializers.ValidationError('Sender not found')

        if not card:
            raise serializers.ValidationError('Card not found')

        if BlackListCard.objects.filter(card=card).exists():
            raise serializers.ValidationError('Card blacklisted')

        receiver = card.account
        amount = data['amount']

        if sender == receiver:
            raise serializers.ValidationError('Cannot transfer to yourself')

        if amount <= 0:
            raise serializers.ValidationError('Amount must be more than 0')

        if sender.balance < amount:
            raise serializers.ValidationError('Not enough money')

        if BlackListAccount.objects.filter(account=sender).exists():
            raise serializers.ValidationError('Sender blacklisted')

        if BlackListAccount.objects.filter(account=receiver).exists():
            raise serializers.ValidationError('Receiver blacklisted')

        with transaction.atomic():
            _move_account_balance(sender, receiver, amount)

            return Transaction.objects.create(
                type='card',
                sender=sender,
                reciver=receiver,
                amount=amount,
                cuur_balance_sender=sender.balance,
                cuur_balance_reciver=receiver.balance,
                description=data.get('description', ''),
                status='completed'
            )


class TransferByPhoneSerializer(serializers.Serializer):
    receiver_phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False)

    def create(self, data):
        sender = Account.objects.filter(
            user=self.context['request'].user
        ).first()

        user = User.objects.filter(
            phone_num=data['receiver_phone']
        ).first()

        if not sender:
            raise serializers.ValidationError('Sender not found')

        if not user:
            raise serializers.ValidationError('User not found')

        receiver = Account.objects.filter(user=user).first()

        if not receiver:
            raise serializers.ValidationError('Receiver not found')

        amount = data['amount']

        if sender == receiver:
            raise serializers.ValidationError('Cannot transfer to yourself')

        if amount <= 0:
            raise serializers.ValidationError('Amount must be more than 0')

        if sender.balance < amount:
            raise serializers.ValidationError('Not enough money')

        if BlackListAccount.objects.filter(account=sender).exists():
            raise serializers.ValidationError('Sender blacklisted')

        if BlackListAccount.objects.filter(account=receiver).exists():
            raise serializers.ValidationError('Receiver blacklisted')

        with transaction.atomic():
            _move_account_balance(sender, receiver, amount)

            return Transaction.objects.create(
                type='phone_num',
                sender=sender,
                reciver=receiver,
                amount=amount,
                cuur_balance_sender=sender.balance,
                cuur_balance_reciver=receiver.balance,
                description=data.get('description', ''),
                status='completed'
            )


class InsideTransferByPhoneSerializer(serializers.Serializer):
    receiver_phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False)

    def create(self, data):
        sender = Account.objects.filter(
            user=self.context['request'].user
        ).first()

        user = User.objects.filter(
            phone_num=data['receiver_phone']
        ).first()

        if not sender or not user:
            raise serializers.ValidationError('User not found')

        receiver = Account.objects.filter(user=user).first()

        if not receiver:
            raise serializers.ValidationError('Receiver not found')

        amount = data['amount']

        if sender == receiver:
            raise serializers.ValidationError('Cannot transfer to yourself')

        if amount <= 0:
            raise serializers.ValidationError('Amount must be more than 0')

        if sender.balance < amount:
            raise serializers.ValidationError('Not enough money')

        if BlackListAccount.objects.filter(account=sender).exists():
            raise serializers.ValidationError('Sender blacklisted')

        if BlackListAccount.objects.filter(account=receiver).exists():
            raise serializers.ValidationError('Receiver blacklisted')

        with transaction.atomic():
            _move_account_balance(sender, receiver, amount)

            return TransactionInside.objects.create(
                type='phone_num',
                sender=sender.user.phone_num,
                reciver=receiver.user.phone_num,
                amount=amount,
                cuur_balance_sender=sender.balance,
                cuur_balance_reciver=receiver.balance,
                description=data.get('description', ''),
                status='completed'
            )


class InsideTransferByCardSerializer(serializers.Serializer):
    receiver_card_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False)

    def create(self, data):
        sender = Account.objects.filter(
            user=self.context['request'].user
        ).first()

        card = Card.objects.filter(
            card_id=data['receiver_card_id']
        ).first()

        if not sender or not card:
            raise serializers.ValidationError('Card not found')

        if BlackListCard.objects.filter(card=card).exists():
            raise serializers.ValidationError('Card blacklisted')

        receiver = card.account
        amount = data['amount']

        if sender == receiver:
            raise serializers.ValidationError('Cannot transfer to yourself')

        if amount <= 0:
            raise serializers.ValidationError('Amount must be more than 0')

        if sender.balance < amount:
            raise serializers.ValidationError('Not enough money')

        if BlackListAccount.objects.filter(account=sender).exists():
            raise serializers.ValidationError('Sender blacklisted')

        if BlackListAccount.objects.filter(account=receiver).exists():
            raise serializers.ValidationError('Receiver blacklisted')

        with transaction.atomic():
            _move_account_balance(sender, receiver, amount)

            return TransactionInside.objects.create(
                type='card',
                sender=sender.user.phone_num,
                reciver=card.card_id,
                amount=amount,
                cuur_balance_sender=sender.balance,
                cuur_balance_reciver=receiver.balance,
                description=data.get('description', ''),
                status='completed'
            )


class GetCreditInputSerializer(serializers.Serializer):
    card_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    procent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'))

    def create(self, data):
        card = Card.objects.filter(
            card_id=data['card_id']
        ).first()

        if not card:
            raise serializers.ValidationError('Card not found')

        if card.account.user != self.context['request'].user:
            raise serializers.ValidationError('Not your card')

        if BlackListCard.objects.filter(card=card).exists():
            raise serializers.ValidationError('Card blacklisted')

        if BlackListAccount.objects.filter(account=card.account).exists():
            raise serializers.ValidationError('Account blacklisted')

        if card.card_name != 'credit':
            raise serializers.ValidationError('Card must be credit')

        with transaction.atomic():
            credit = GetCredit.objects.create(
                card_id=card,
                amount=data['amount'],
                procent=data['procent'],
                status='approved'
            )

            Card.objects.filter(pk=card.pk).update(balance=F('balance') + data['amount'])
            Account.objects.filter(pk=card.account_id).update(
                balance=F('balance') + data['amount']
            )

        return credit


class PutDepositInputSerializer(serializers.Serializer):
    card_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    procent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'))

    def create(self, data):
        card = Card.objects.filter(
            card_id=data['card_id']
        ).first()

        if not card:
            raise serializers.ValidationError('Card not found')

        if card.account.user != self.context['request'].user:
            raise serializers.ValidationError('Not your card')

        if BlackListCard.objects.filter(card=card).exists():
            raise serializers.ValidationError('Card blacklisted')

        if BlackListAccount.objects.filter(account=card.account).exists():
            raise serializers.ValidationError('Account blacklisted')

        if card.balance < data['amount'] or card.account.balance < data['amount']:
            raise serializers.ValidationError('Not enough money')

        with transaction.atomic():
            deposit = PutDeposit.objects.create(
                card_id=card,
                amount=data['amount'],
                procent=data['procent'],
                status='active'
            )

            if not Account.objects.filter(
                pk=card.account_id, balance__gte=data['amount']
            ).update(balance=F('balance') - data['amount']):
                raise serializers.ValidationError('Not enough money')
            if not Card.objects.filter(
                pk=card.pk, balance__gte=data['amount']
            ).update(balance=F('balance') - data['amount']):
                raise serializers.ValidationError('Not enough money')

        return deposit


class BlackListAccountInputSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    description = serializers.CharField(required=False)

    def create(self, data):
        account = Account.objects.filter(id=data['account_id']).first()

        if not account:
            raise serializers.ValidationError('Account not found')

        return BlackListAccount.objects.create(
            account=account,
            description=data.get('description', '')
        )


class BlackListCardInputSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    description = serializers.CharField(required=False)

    def create(self, data):
        card = Card.objects.filter(id=data['card_id']).first()

        if not card:
            raise serializers.ValidationError('Card not found')

        return BlackListCard.objects.create(
            card=card,
            description=data.get('description', '')
        )
