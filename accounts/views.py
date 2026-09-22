from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import User
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer,
    LoginOTPSerializer, UserSerializer
)
from banck.serializers import AccountSerializer


class SendOTPView(generics.CreateAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=SendOTPSerializer, responses={200: 'OTP sent'})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)


class VerifyOTPView(generics.CreateAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=VerifyOTPSerializer, responses={201: AccountSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            'message': 'Account created successfully',
            'token': result['token'],
            'account': AccountSerializer(result['account']).data,
        }, status=status.HTTP_201_CREATED)


class LoginOTPView(generics.CreateAPIView):
    serializer_class = LoginOTPSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=LoginOTPSerializer, responses={200: 'Token'})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            'message': 'Login successful',
            'token': result['token'],
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
