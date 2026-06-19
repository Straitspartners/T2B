from django.urls import path
from . import views
from .views import approve_invoices_in_zoho

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
    path('users/taxes/', views.receive_tax),
    path('users/purchases/', views.receive_purchases),
    path('users/bills/', views.receive_purchases),
    path('users/payments/', views.receive_payments),
    path('users/credit-notes/', views.receive_credit_notes),
    path('users/vendor-credits/', views.receive_vendor_credits),
    path('users/journals/', views.receive_journals),
    path('users/expenses/', views.receive_expenses),
    path('users/opening-balances/', views.receive_opening_balances),
    path('migration-status-all/', views.migration_status_all),

    # --- Marks Invoice Approved ---
    path('approve-invoices/', approve_invoices_in_zoho, name='approve_invoices'),

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

    path('customerdashboard/', views.customer_dashboard),
    path('vendordashboard/', views.vendor_dashboard),
    path('coadashboard/', views.coa_dashboard),
    path('itemsdashboard/', views.items_dashboard),
    path('invoicedashboard/', views.invoice_dashboard),
    path('receiptdashboard/', views.receipt_dashboard),
    path('creditnotedashboard/', views.credit_note_dashboard),
    path('billdashboard/', views.bill_dashboard),
    path('paymentmadedashboard/', views.payment_made_dashboard),
    path('vendorcreditdashboard/', views.vendor_credit_dashboard),
    path('expensedashboard/', views.expense_dashboard),
    path('journaldashboard/', views.journal_dashboard),

    # --- Settings page ---
    path('settings/zoho-status/', views.get_zoho_connection_status),
    path('settings/test-tally/', views.test_tally_connection),
    path('settings/change-password/', views.change_password),
    path('settings/clear-migration/', views.clear_migration_data),
]