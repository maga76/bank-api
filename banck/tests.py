from datetime import date, timedelta
from decimal import Decimal

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Account, BlackListCard, Card


class BankingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_num='992900000010', username='sender', password='test-password',
            is_verified=True,
        )
        self.other_user = User.objects.create_user(
            phone_num='992900000011', username='receiver', password='test-password',
            is_verified=True,
        )
        self.sender = Account.objects.create(
            user=self.user, fname='Send', lname='User', passport_id='A1',
            balance=Decimal('100.00'),
        )
        self.receiver = Account.objects.create(
            user=self.other_user, fname='Receive', lname='User', passport_id='B1',
        )
        self.card = Card.objects.create(
            account=self.sender, card_id='1111222233334444',
            card_name='credit', cvv='123',
            expair=date.today() + timedelta(days=365),
            balance=Decimal('100.00'),
        )
        self.receiver_card = Card.objects.create(
            account=self.receiver, card_id='5555666677778888',
            card_name='credit', cvv='456',
            expair=date.today() + timedelta(days=365),
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)

    def test_transfer_by_phone_uses_authenticated_sender(self):
        response = self.client.post('/api/bank/transfer/phone/', {
            'receiver_phone': self.other_user.phone_num,
            'amount': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['type'], 'phone_num')
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        self.assertEqual(self.sender.balance, Decimal('90.00'))
        self.assertEqual(self.receiver.balance, Decimal('10.00'))

    def test_negative_credit_and_deposit_are_rejected(self):
        for url in ('/api/bank/credit/', '/api/bank/deposit/'):
            with self.subTest(url=url):
                response = self.client.post(url, {
                    'card_id': self.card.card_id,
                    'amount': '-10.00',
                    'procent': '1.00',
                }, format='json')
                self.assertEqual(response.status_code, 400)

        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('100.00'))

    def test_card_balance_cannot_be_changed_through_card_endpoint(self):
        response = self.client.patch('/api/bank/card/' + str(self.card.pk) + '/', {
            'balance': '1000000.00',
            'cvv': '999',
            'card_id': '9999888877776666',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertEqual(self.card.cvv, '123')
        self.assertEqual(self.card.card_id, '1111222233334444')

    def test_card_transfer_appears_in_recipient_inside_history(self):
        response = self.client.post('/api/bank/transfer/inside/card/', {
            'receiver_card_id': self.receiver_card.card_id,
            'amount': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        receiver_token = Token.objects.create(user=self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + receiver_token.key)
        history = self.client.get('/api/bank/transactions/inside/')
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.data), 1)

    def test_blacklisted_card_cannot_be_used_for_transfer_or_credit(self):
        BlackListCard.objects.create(card=self.receiver_card)
        response = self.client.post('/api/bank/transfer/card/', {
            'receiver_card_id': self.receiver_card.card_id,
            'amount': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 400)

        BlackListCard.objects.create(card=self.card)
        response = self.client.post('/api/bank/credit/', {
            'card_id': self.card.card_id,
            'amount': '10.00',
            'procent': '1.00',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_credit_and_deposit_succeed_with_positive_amounts(self):
        credit = self.client.post('/api/bank/credit/', {
            'card_id': self.card.card_id,
            'amount': '10.00',
            'procent': '1.00',
        }, format='json')
        self.assertEqual(credit.status_code, 201)

        deposit = self.client.post('/api/bank/deposit/', {
            'card_id': self.card.card_id,
            'amount': '5.00',
            'procent': '1.00',
        }, format='json')
        self.assertEqual(deposit.status_code, 201)
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('105.00'))

    def test_inside_phone_transfer_succeeds(self):
        response = self.client.post('/api/bank/transfer/inside/phone/', {
            'receiver_phone': self.other_user.phone_num,
            'amount': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['type'], 'phone_num')
