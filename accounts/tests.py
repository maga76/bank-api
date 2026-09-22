import json
from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import User
from .serializers import VerifyOTPSerializer


class BearerAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_num='992900000001', username='test-user', password='test-password',
            is_verified=True,
        )
        self.token = Token.objects.create(user=self.user)

    def test_profile_requires_valid_bearer_token(self):
        url = '/api/accounts/profile/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['WWW-Authenticate'], 'Bearer')

        response = self.client.get(url, HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.assertEqual(response.status_code, 401)

        response = self.client.get(url, HTTP_AUTHORIZATION='Bearer invalid-token')
        self.assertEqual(response.status_code, 401)

        response = self.client.get(url, HTTP_AUTHORIZATION='Bearer ' + self.token.key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.id)

    def test_otp_login_issues_a_usable_bearer_token(self):
        self.user.otp = '123456'
        self.user.otp_created_at = timezone.now()
        self.user.save(update_fields=['otp', 'otp_created_at'])

        response = self.client.post('/api/accounts/login/', {
            'phone_num': self.user.phone_num,
            'otp': '123456',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['token'], self.token.key)

        response = self.client.get(
            '/api/bank/transactions/',
            HTTP_AUTHORIZATION='Bearer ' + response.data['token'],
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_otp_verification_issues_a_usable_bearer_token(self):
        phone_num = '992900000002'
        response = self.client.post('/api/accounts/auth/', {
            'phone_num': phone_num,
        }, format='json')
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(phone_num=phone_num)
        response = self.client.post('/api/accounts/verify/', {
            'phone_num': phone_num,
            'otp': user.otp,
            'fname': 'Test',
            'lname': 'User',
            'passport_id': 'AB123456',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        profile = self.client.get(
            '/api/accounts/profile/',
            HTTP_AUTHORIZATION='Bearer ' + response.data['token'],
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data['id'], user.id)

    def test_swagger_describes_bearer_auth_and_public_otp_routes(self):
        response = self.client.get('/swagger.json')
        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.content)

        self.assertEqual(schema['security'], [{'Bearer': []}])
        self.assertEqual(schema['securityDefinitions']['Bearer']['name'], 'Authorization')
        for path in ('/accounts/auth/', '/accounts/verify/', '/accounts/login/'):
            self.assertEqual(schema['paths'][path]['post']['security'], [])

        login_response = schema['paths']['/accounts/login/']['post']['responses']['200']
        self.assertEqual(login_response['schema']['$ref'], '#/definitions/LoginOTPResponse')
        self.assertIn('token', schema['definitions']['LoginOTPResponse']['properties'])

        lookup_parameters = schema['paths']['/bank/card/lookup/']['get']['parameters']
        self.assertEqual({parameter['name'] for parameter in lookup_parameters}, {'number', 'phone'})

    def test_verification_of_existing_account_returns_validation_error(self):
        self.user.otp = '123456'
        self.user.otp_created_at = timezone.now()
        self.user.save(update_fields=['otp', 'otp_created_at'])
        response = self.client.post('/api/accounts/verify/', {
            'phone_num': self.user.phone_num,
            'otp': '123456',
            'fname': 'Test',
            'lname': 'User',
            'passport_id': 'AB123456',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_failed_account_creation_does_not_consume_otp(self):
        user = User.objects.create_user(phone_num='992900000003', username='new-user')
        user.otp = '123456'
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp', 'otp_created_at'])
        serializer = VerifyOTPSerializer(data={
            'phone_num': user.phone_num,
            'otp': '123456',
            'fname': 'Test',
            'lname': 'User',
            'passport_id': 'AB123456',
        })
        self.assertTrue(serializer.is_valid())
        with patch('banck.models.Account.objects.create', side_effect=RuntimeError('database error')):
            with self.assertRaises(RuntimeError):
                serializer.save()
        user.refresh_from_db()
        self.assertFalse(user.is_verified)
        self.assertEqual(user.otp, '123456')

    def test_expired_otp_cannot_be_used_for_login(self):
        self.user.otp = '123456'
        self.user.otp_created_at = timezone.now() - timedelta(minutes=6)
        self.user.save(update_fields=['otp', 'otp_created_at'])

        response = self.client.post('/api/accounts/login/', {
            'phone_num': self.user.phone_num,
            'otp': '123456',
        }, format='json')
        self.assertEqual(response.status_code, 400)
