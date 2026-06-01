from django.urls import path
from . import views

urlpatterns = [
    # --- User Auth ---
    path('register/', views.register_user),
    path('signin/', views.signin_user),

    # --- Agent Token ---
    path('generate_token_agent/', views.generate_agent_token),

    # --- Zoho Connection ---
    path('connect-zoho/', views.connect_zoho),

    # --- Sync Agent Data Receivers ---
    path('users/ledgers/', views.receive_customers),
    path('users/vendors/', views.receive_vendors),
    path('users/accounts/', views.receive_accounts),
    path('users/items/', views.receive_items),
    path('users/invoices/', views.receive_invoices),
    path('users/receipts/', views.receive_receipts),

    # --- Legacy paths ---
    path('receive-customers/', views.receive_customers),
    path('next-task/', views.get_next_task),

    # --- Dashboard & Migration ---
    path('data-migration-status/', views.data_migration_status),
    path('total-records/', views.total_records),
    path('push-to-zoho/', views.push_to_zoho),

    # --- Masters & Transactions pages ---
    path('masters/', views.get_masters),
    path('transactions/', views.get_transactions),
]