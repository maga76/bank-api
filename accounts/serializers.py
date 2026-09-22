import random
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import User


class SendOTPSerializer(serializers.Serializer):
    phone_num = serializers.CharField(max_length=20)

    def create(self, validated_data):
        phone_num = validated_data['phone_num']
        otp = str(random.randint(100000, 999999))

        user, created = User.objects.get_or_create(phone_num=phone_num, defaults={'username': phone_num})
        user.otp = otp
        user.save()

        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP code is: {otp}',
            from_email=None,
            recipient_list=[phone_num],
            fail_silently=True,
        )
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone_num = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)
    fname = serializers.CharField(max_length=100)
    lname = serializers.CharField(max_length=100)
    passport_id = serializers.CharField(max_length=50)

    def validate(self, attrs):
        try:
            user = User.objects.get(phone_num=attrs['phone_num'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'User not found'})

        if user.otp != attrs['otp']:
            raise serializers.ValidationError({'error': 'Invalid OTP'})

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        user.is_verified = True
        user.otp = None
        user.save()

        from banck.models import Account
        account = Account.objects.create(
            user=user,
            fname=validated_data['fname'],
            lname=validated_data['lname'],
            passport_id=validated_data['passport_id'],
        )

        token, _ = Token.objects.get_or_create(user=user)
        return {'account': account, 'token': token.key}


class LoginOTPSerializer(serializers.Serializer):
    phone_num = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(phone_num=attrs['phone_num'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'User not found'})

        if user.otp != attrs['otp']:
            raise serializers.ValidationError({'error': 'Invalid OTP'})

        if not user.is_verified:
            raise serializers.ValidationError({'error': 'User not verified'})

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        user.otp = None
        user.save()

        token, _ = Token.objects.get_or_create(user=user)
        return {'token': token.key}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_num', 'username', 'is_verified']
