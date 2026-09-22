import json
from datetime import date, timedelta
from decimal import Decimal

from rest_framework.authtoken.models import Token
from rest_framework import serializers
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Account, BlackListAccount, BlackListCard, Card, PutDeposit
from .serializers import _move_account_balance


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

    def test_swagger_post_responses_match_returned_models(self):
        response = self.client.get('/swagger.json')
        self.assertEqual(response.status_code, 200)
        paths = json.loads(response.content)['paths']
        expected = {
            '/bank/transfer/card/': 'Transaction',
            '/bank/transfer/phone/': 'Transaction',
            '/bank/transfer/inside/card/': 'TransactionInside',
            '/bank/transfer/inside/phone/': 'TransactionInside',
            '/bank/credit/': 'GetCredit',
            '/bank/deposit/': 'PutDeposit',
            '/bank/blacklist/account/add/': 'BlackListAccount',
            '/bank/blacklist/card/add/': 'BlackListCard',
        }
        for path, model in expected.items():
            with self.subTest(path=path):
                schema = paths[path]['post']['responses']['201']['schema']
                self.assertEqual(schema['$ref'], f'#/definitions/{model}')

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

    def test_card_responses_do_not_expose_cvv(self):
        for url in ('/api/bank/card/', f'/api/bank/card/{self.card.pk}/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                cards = response.data if isinstance(response.data, list) else [response.data]
                self.assertTrue(cards)
                self.assertTrue(all('cvv' not in card for card in cards))

    def test_card_lookup_returns_number_for_both_search_methods(self):
        for query in (f'number={self.receiver_card.card_id}',
                      f'phone={self.other_user.phone_num}'):
            with self.subTest(query=query):
                response = self.client.get(f'/api/bank/card/lookup/?{query}')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['card_number'], self.receiver_card.card_id)
                self.assertEqual(response.data['card_id'], self.receiver_card.pk)

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
        self.sender.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('105.00'))
        self.assertEqual(self.sender.balance, Decimal('105.00'))

    def test_deposit_cannot_spend_more_than_account_balance(self):
        self.sender.balance = Decimal('2.00')
        self.sender.save(update_fields=['balance'])
        response = self.client.post('/api/bank/deposit/', {
            'card_id': self.card.card_id,
            'amount': '5.00',
            'procent': '1.00',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertFalse(PutDeposit.objects.exists())

    def test_transfer_uses_current_balance_when_objects_are_stale(self):
        Account.objects.filter(pk=self.sender.pk).update(balance=Decimal('8.00'))
        with self.assertRaises(serializers.ValidationError):
            _move_account_balance(self.sender, self.receiver, Decimal('10.00'))
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        self.assertEqual(self.sender.balance, Decimal('8.00'))
        self.assertEqual(self.receiver.balance, Decimal('0.00'))

        Account.objects.filter(pk=self.receiver.pk).update(balance=Decimal('5.00'))
        _move_account_balance(self.sender, self.receiver, Decimal('3.00'))
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        self.assertEqual(self.sender.balance, Decimal('5.00'))
        self.assertEqual(self.receiver.balance, Decimal('8.00'))

    def test_blacklisted_account_cannot_use_credit_or_deposit(self):
        BlackListAccount.objects.create(account=self.sender)
        for url in ('/api/bank/credit/', '/api/bank/deposit/'):
            with self.subTest(url=url):
                response = self.client.post(url, {
                    'card_id': self.card.card_id,
                    'amount': '5.00',
                    'procent': '1.00',
                }, format='json')
                self.assertEqual(response.status_code, 400)

    def test_inside_phone_transfer_succeeds(self):
        response = self.client.post('/api/bank/transfer/inside/phone/', {
            'receiver_phone': self.other_user.phone_num,
            'amount': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['type'], 'phone_num')
