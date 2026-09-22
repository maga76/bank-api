import random
from django.db import transaction
from rest_framework import serializers
from accounts.models import User
from .models import *


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'fname', 'lname', 'passport_id', 'balance']


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'card_id', 'card_name', 'balance', 'cvv', 'created_at', 'expair']

    def create(self, data):
        user = self.context['request'].user
        account = Account.objects.filter(user=user).first()

        if not account:
            raise serializers.ValidationError('Account not found')

        while True:
            card_id = str(random.randint(1000000000000000, 9999999999999999))
            if not Card.objects.filter(card_id=card_id).exists():
                break

        return Card.objects.create(
            account=account,
            card_id=card_id,
            card_name=data.get('card_name', 'simple'),
            cvv=str(random.randint(100, 999)),
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
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()

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
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()

            return Transaction.objects.create(
                type='phone',
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
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()

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
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()

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
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    procent = serializers.DecimalField(max_digits=5, decimal_places=2)

    def create(self, data):
        card = Card.objects.filter(
            card_id=data['card_id']
        ).first()

        if not card:
            raise serializers.ValidationError('Card not found')

        if card.account.user != self.context['request'].user:
            raise serializers.ValidationError('Not your card')

        if card.card_name != 'credit':
            raise serializers.ValidationError('Card must be credit')

        with transaction.atomic():
            credit = GetCredit.objects.create(
                card_id=card,
                amount=data['amount'],
                procent=data['procent'],
                status='approved'
            )

            card.balance += data['amount']
            card.account.balance += data['amount']
            card.save()
            card.account.save()

        return credit


class PutDepositInputSerializer(serializers.Serializer):
    card_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    procent = serializers.DecimalField(max_digits=5, decimal_places=2)

    def create(self, data):
        card = Card.objects.filter(
            card_id=data['card_id']
        ).first()

        if not card:
            raise serializers.ValidationError('Card not found')

        if card.account.user != self.context['request'].user:
            raise serializers.ValidationError('Not your card')

        if card.balance < data['amount']:
            raise serializers.ValidationError('Not enough money')

        with transaction.atomic():
            deposit = PutDeposit.objects.create(
                card_id=card,
                amount=data['amount'],
                procent=data['procent'],
                status='active'
            )

            card.balance -= data['amount']
            card.save()

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
