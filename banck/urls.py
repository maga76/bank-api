from django.urls import path
from . import views

urlpatterns = [
    path('card/', views.CardListCreateView.as_view(), name='card_list_create'),
    path('card/<int:pk>/', views.CardDetailView.as_view(), name='card_detail'),
    path('card/lookup/', views.CardLookupView.as_view(), name='card_lookup'),

    path('transfer/card/', views.TransferByCardView.as_view(), name='transfer_by_card'),
    path('transfer/phone/', views.TransferByPhoneView.as_view(), name='transfer_by_phone'),
    path('transfer/inside/phone/', views.InsideTransferByPhoneView.as_view(), name='inside_transfer_phone'),
    path('transfer/inside/card/', views.InsideTransferByCardView.as_view(), name='inside_transfer_card'),

    path('credit/', views.GetCreditView.as_view(), name='get_credit'),
    path('deposit/', views.PutDepositView.as_view(), name='put_deposit'),

    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/inside/', views.InsideTransactionListView.as_view(), name='inside_transaction_list'),

    path('blacklist/account/add/', views.AddAccountToBlacklistView.as_view(), name='add_account_blacklist'),
    path('blacklist/card/add/', views.AddCardToBlacklistView.as_view(), name='add_card_blacklist'),
    path('blacklist/account/<int:pk>/remove/', views.RemoveAccountFromBlacklistView.as_view(), name='remove_account_blacklist'),
    path('blacklist/card/<int:pk>/remove/', views.RemoveCardFromBlacklistView.as_view(), name='remove_card_blacklist'),
    path('blacklist/accounts/', views.BlacklistAccountsListView.as_view(), name='blacklist_accounts_list'),
    path('blacklist/cards/', views.BlacklistCardsListView.as_view(), name='blacklist_cards_list'),

    path('admin/accounts/', views.AdminAllAccountsView.as_view(), name='admin_all_accounts'),
    path('admin/cards/', views.AdminAllCardsView.as_view(), name='admin_all_cards'),
    path('admin/transactions/', views.AdminAllTransactionsView.as_view(), name='admin_all_transactions'),
    path('admin/account/<int:pk>/', views.AdminAccountDetailView.as_view(), name='admin_account_detail'),
    path('admin/account/<int:pk>/delete/', views.AdminDeleteAccountView.as_view(), name='admin_delete_account'),
    path('admin/card/<int:pk>/delete/', views.AdminDeleteCardView.as_view(), name='admin_delete_card'),
]
