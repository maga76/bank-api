from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from accounts.models import User
from .models import Card, Transaction, Account
from .models import BlackListAccount, BlackListCard
from .filters import own_cards, own_transactions, own_inside_transactions
from .permissions import IsOwner
from .serializers import *

class CardListCreateView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        return own_cards(self.request.user)


class CardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Card.objects.none()
        return own_cards(self.request.user)


class CardLookupView(generics.GenericAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Find a card by number or phone',
        operation_description='Provide either number or phone. Requires a Bearer token.',
        manual_parameters=[
            openapi.Parameter('number', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('phone', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'card_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'card_number': openapi.Schema(type=openapi.TYPE_STRING),
                    'card_type': openapi.Schema(type=openapi.TYPE_STRING),
                    'owner': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            400: 'Provide number or phone',
            404: 'Card or user not found',
        },
    )
    def get(self, request):
        number = request.query_params.get('number')
        phone = request.query_params.get('phone')

        if number:
            number = number.strip()

            card = Card.objects.filter(card_id=number).first()

            if card == None:
                return Response({
                    'detail': 'Card not found.'
                }, status=404)

            data = {
                'card_id': card.id,
                'card_number': card.card_id,
                'card_type': card.card_name,
                'owner': card.account.user.phone_num
            }

            return Response(data, status=200)

        if phone:
            phone = phone.strip()

            user = User.objects.filter(phone_num=phone).first()

            if user == None:
                return Response({'detail': 'User not found.'}, status=404)

            card = Card.objects.filter(account__user=user).first()

            if card == None:
                return Response({'detail': 'Recipient has no cards.'}, status=404)

            data = {
                'card_id': card.id,
                'card_number': card.card_id,
                'card_type': card.card_name,
                'owner': user.phone_num
            }

            return Response(data, status=200)

        return Response({'detail': 'Provide number or phone query param.'}, status=400)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return own_transactions(self.request.user)


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        return own_transactions(self.request.user)


class TransferByCardView(generics.CreateAPIView):
    serializer_class = TransferByCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: TransactionSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transaction = serializer.save()

        data = TransactionSerializer(transaction).data

        return Response(data, status=201)


class TransferByPhoneView(generics.CreateAPIView):
    serializer_class = TransferByPhoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: TransactionSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transaction = serializer.save()

        data = TransactionSerializer(transaction).data

        return Response(data, status=201)


class InsideTransferByPhoneView(generics.CreateAPIView):
    serializer_class = InsideTransferByPhoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: TransactionInsideSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transaction = serializer.save()

        data = TransactionInsideSerializer(transaction).data

        return Response(data, status=201)


class InsideTransferByCardView(generics.CreateAPIView):
    serializer_class = InsideTransferByCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: TransactionInsideSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        transaction = serializer.save()

        data = TransactionInsideSerializer(transaction).data

        return Response(data, status=201)


class GetCreditView(generics.CreateAPIView):
    serializer_class = GetCreditInputSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: GetCreditSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        credit = serializer.save()

        data = GetCreditSerializer(credit).data

        return Response(data, status=201)


class PutDepositView(generics.CreateAPIView):
    serializer_class = PutDepositInputSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={201: PutDepositSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        deposit = serializer.save()

        data = PutDepositSerializer(deposit).data

        return Response(data, status=201)


class InsideTransactionListView(generics.ListAPIView):
    serializer_class = TransactionInsideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TransactionInside.objects.none()
        return own_inside_transactions(self.request.user)


class AddAccountToBlacklistView(generics.CreateAPIView):
    serializer_class = BlackListAccountInputSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(responses={201: BlackListAccountSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        account = serializer.save()

        data = BlackListAccountSerializer(account).data

        return Response(data, status=201)


class AddCardToBlacklistView(generics.CreateAPIView):
    serializer_class = BlackListCardInputSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(responses={201: BlackListCardSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        card = serializer.save()

        data = BlackListCardSerializer(card).data

        return Response(data, status=201)


class RemoveAccountFromBlacklistView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = BlackListAccount.objects.all()


class RemoveCardFromBlacklistView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = BlackListCard.objects.all()


class BlacklistAccountsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = BlackListAccountSerializer
    queryset = BlackListAccount.objects.all()


class BlacklistCardsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = BlackListCardSerializer
    queryset = BlackListCard.objects.all()


class AdminAllAccountsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class AdminAllCardsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CardSerializer
    queryset = Card.objects.all()


class AdminAllTransactionsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all().order_by('-created_at')


class AdminAccountDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class AdminDeleteAccountView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Account.objects.all()


class AdminDeleteCardView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Card.objects.all()
