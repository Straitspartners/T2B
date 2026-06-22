from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('register/',           views.register_user,         name='register'),
    path('login/',              views.signin_user,           name='login'),
    path('agent-token/',        views.generate_agent_token,  name='agent_token'),

    # ── Zoho Connection ───────────────────────────────────────────────────────
    path('connect-zoho/',              views.connect_zoho,        name='connect_zoho'),
    path('zoho/exchange-code/',        views.exchange_zoho_code,  name='exchange_zoho_code'),  # NEW
    path('zoho/connection-status/',    views.get_zoho_connection_status, name='zoho_status'),

    # ── Agent Data Receivers ──────────────────────────────────────────────────
    path('receive-customers/',         views.receive_customers,         name='receive_customers'),
    path('receive-vendors/',           views.receive_vendors,           name='receive_vendors'),
    path('receive-accounts/',          views.receive_accounts,          name='receive_accounts'),
    path('receive-items/',             views.receive_items,             name='receive_items'),
    path('receive-invoices/',          views.receive_invoices,          name='receive_invoices'),
    path('receive-receipts/',          views.receive_receipts,          name='receive_receipts'),
    path('receive-purchases/',         views.receive_purchases,         name='receive_purchases'),
    path('receive-payments/',          views.receive_payments,          name='receive_payments'),
    path('receive-credit-notes/',      views.receive_credit_notes,      name='receive_credit_notes'),
    path('receive-vendor-credits/',    views.receive_vendor_credits,    name='receive_vendor_credits'),
    path('receive-journals/',          views.receive_journals,          name='receive_journals'),
    path('receive-expenses/',          views.receive_expenses,          name='receive_expenses'),
    path('receive-tax/',               views.receive_tax,               name='receive_tax'),
    path('receive-opening-balances/',  views.receive_opening_balances,  name='receive_opening_balances'),

    # ── Push to Zoho ──────────────────────────────────────────────────────────
    path('push-to-zoho/',              views.push_to_zoho,              name='push_to_zoho'),
    path('approve-invoices/',          views.approve_invoices_in_zoho,  name='approve_invoices'),

    # ── Dashboard & Status ────────────────────────────────────────────────────
    path('migration-status/',          views.data_migration_status,     name='migration_status'),
    path('migration-status-all/',      views.migration_status_all,      name='migration_status_all'),
    path('total-records/',             views.total_records,             name='total_records'),
    path('get-masters/',               views.get_masters,               name='get_masters'),
    path('get-transactions/',          views.get_transactions,          name='get_transactions'),
    path('next-task/',                 views.get_next_task,             name='next_task'),

    # ── Per-model Dashboards ──────────────────────────────────────────────────
    path('dashboard/customers/',       views.customer_dashboard,        name='customer_dashboard'),
    path('dashboard/vendors/',         views.vendor_dashboard,          name='vendor_dashboard'),
    path('dashboard/accounts/',        views.coa_dashboard,             name='coa_dashboard'),
    path('dashboard/items/',           views.items_dashboard,           name='items_dashboard'),
    path('dashboard/invoices/',        views.invoice_dashboard,         name='invoice_dashboard'),
    path('dashboard/receipts/',        views.receipt_dashboard,         name='receipt_dashboard'),
    path('dashboard/credit-notes/',    views.credit_note_dashboard,     name='credit_note_dashboard'),
    path('dashboard/bills/',           views.bill_dashboard,            name='bill_dashboard'),
    path('dashboard/payments-made/',   views.payment_made_dashboard,    name='payment_made_dashboard'),
    path('dashboard/vendor-credits/',  views.vendor_credit_dashboard,   name='vendor_credit_dashboard'),
    path('dashboard/expenses/',        views.expense_dashboard,         name='expense_dashboard'),
    path('dashboard/journals/',        views.journal_dashboard,         name='journal_dashboard'),

    # ── Settings ──────────────────────────────────────────────────────────────
    path('settings/change-password/',  views.change_password,           name='change_password'),
    path('settings/clear-migration/',  views.clear_migration_data,      name='clear_migration'),
    path('settings/test-tally/',       views.test_tally_connection,     name='test_tally'),
]