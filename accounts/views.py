from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import User
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer,
    LoginOTPSerializer, UserSerializer,
    MessageResponseSerializer, VerifyOTPResponseSerializer,
    LoginOTPResponseSerializer,
)
from banck.serializers import AccountSerializer


class SendOTPView(generics.CreateAPIView):
    serializer_class = SendOTPSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary='Request an OTP',
        operation_description='The OTP is printed to the server console in development.',
        security=[],
        responses={200: MessageResponseSerializer, 400: 'Invalid request'},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)


class VerifyOTPView(generics.CreateAPIView):
    serializer_class = VerifyOTPSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary='Verify OTP and create an account',
        security=[],
        responses={201: VerifyOTPResponseSerializer, 400: 'Invalid or expired OTP'},
    )
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
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary='Log in with an OTP',
        security=[],
        responses={200: LoginOTPResponseSerializer, 400: 'Invalid OTP'},
    )
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
