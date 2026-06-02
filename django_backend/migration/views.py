from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import AppUser, Invoice, InvoiceLineItem, Receipt, ZohoConfig
import json
import jwt
import datetime
import bcrypt
import os
import re
from decimal import Decimal, InvalidOperation
import requests as req

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key_here_minimum_32_characters_long")

ZOHO_BOOKS_BASE = "https://www.zohoapis.in/books/v3"


# ---------------- AUTH HELPERS ----------------

def verify_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        raise ValueError('Authentication token not found. Please login again.')
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expired. Please login again.')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token. Please login again.')


def _get_user_by_email_or_username(identifier):
    try:
        return AppUser.objects.get(email=identifier)
    except AppUser.DoesNotExist:
        pass
    try:
        return AppUser.objects.get(username=identifier)
    except AppUser.DoesNotExist:
        return None


def _get_zoho_config(user_email):
    """Retrieve stored Zoho config for this user. Raises ValueError if not found."""
    try:
        return ZohoConfig.objects.get(user_email=user_email)
    except ZohoConfig.DoesNotExist:
        raise ValueError('Zoho Books is not connected. Please connect via the settings page.')


def _refresh_zoho_token(config):
    """
    Use the stored refresh_token to obtain a new access_token from Zoho OAuth.
    Updates the config object in-place and persists to DB.
    Returns the new access_token string.
    """
    resp = req.post(
        'https://accounts.zoho.com/oauth/v2/token',
        params={
            'refresh_token': config.refresh_token,
            'client_id': config.client_id,
            'client_secret': config.client_secret,
            'grant_type': 'refresh_token',
        }
    )
    data = resp.json()
    if 'access_token' not in data:
        raise ValueError(f"Failed to refresh Zoho token: {data.get('error', 'Unknown error')}")
    config.access_token = data['access_token']
    config.save(update_fields=['access_token'])
    return config.access_token


def _zoho_headers(access_token):
    return {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json',
    }


def _zoho_get(url, config):
    """GET helper that auto-refreshes on 401."""
    resp = req.get(url, headers=_zoho_headers(config.access_token))
    if resp.status_code == 401:
        _refresh_zoho_token(config)
        resp = req.get(url, headers=_zoho_headers(config.access_token))
    return resp


def _zoho_post(url, payload, config):
    """POST helper that auto-refreshes on 401."""
    resp = req.post(url, json=payload, headers=_zoho_headers(config.access_token))
    if resp.status_code == 401:
        _refresh_zoho_token(config)
        resp = req.post(url, json=payload, headers=_zoho_headers(config.access_token))
    return resp


def _zoho_put(url, payload, config):
    """PUT helper that auto-refreshes on 401."""
    resp = req.put(url, json=payload, headers=_zoho_headers(config.access_token))
    if resp.status_code == 401:
        _refresh_zoho_token(config)
        resp = req.put(url, json=payload, headers=_zoho_headers(config.access_token))
    return resp


def _find_existing_contact(name, contact_type, config):
    """Return contact_id if a contact with this name already exists in Zoho, else None."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}&contact_name={name}&contact_type={contact_type}"
    resp = _zoho_get(url, config)
    if resp.status_code == 200:
        contacts = resp.json().get('contacts', [])
        if contacts:
            return contacts[0]['contact_id']
    return None


# ---------------- LINE ITEM HELPERS ----------------

def _parse_quantity(raw_qty):
    """
    Parse a quantity string like "2 Nos", "5 Kg", "3.5 Box" into (Decimal, str).

    Returns:
        (qty_value: Decimal, qty_unit: str)

    Examples:
        "1 Nos"  → (Decimal('1'), 'Nos')
        "2.5 Kg" → (Decimal('2.5'), 'Kg')
        "3"      → (Decimal('3'), 'Nos')   # unit defaults to 'Nos'
        ""       → (Decimal('1'), 'Nos')   # fallback
    """
    raw = (raw_qty or '').strip()
    if not raw:
        return Decimal('1'), 'Nos'

    # Match leading number (int or decimal), then optional whitespace + unit text
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(.*)$', raw)
    if not match:
        return Decimal('1'), 'Nos'

    try:
        qty_value = Decimal(match.group(1))
    except InvalidOperation:
        qty_value = Decimal('1')

    qty_unit = match.group(2).strip() or 'Nos'
    return qty_value, qty_unit


def _derive_rate(amount, qty_value):
    """
    Derive unit rate from total line amount and quantity.
    Returns Decimal. Avoids division by zero (returns amount as rate if qty is 0).
    """
    try:
        amount_d = Decimal(str(amount))
        qty_d = Decimal(str(qty_value))
        if qty_d == 0:
            return amount_d
        return (amount_d / qty_d).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError):
        return Decimal('0')


def _save_line_items(invoice, raw_line_items):
    """
    Delete existing line items for this invoice and recreate from raw_line_items.

    Each item in raw_line_items is expected to look like:
        {
            "item_name": "Product A",
            "quantity": "2 Nos",
            "amount": "500.00"
        }
    """
    invoice.line_items.all().delete()

    items_to_create = []
    for item in raw_line_items:
        raw_qty = item.get('quantity', '1 Nos')
        qty_value, qty_unit = _parse_quantity(raw_qty)

        try:
            amount = Decimal(str(item.get('amount', '0')))
        except InvalidOperation:
            amount = Decimal('0')

        rate = _derive_rate(amount, qty_value)

        items_to_create.append(InvoiceLineItem(
            invoice=invoice,
            item_name=item.get('item_name', ''),
            quantity_raw=raw_qty,
            qty_value=qty_value,
            qty_unit=qty_unit,
            amount=amount,
            rate=rate,
        ))

    if items_to_create:
        InvoiceLineItem.objects.bulk_create(items_to_create)


def _build_zoho_line_items(invoice):
    """
    Build the line_items list expected by the Zoho Books API from stored InvoiceLineItems.

    If no line items exist (legacy data), falls back to a single synthetic line
    derived from the invoice total minus taxes.

    Zoho line item shape:
        {
            "name": "Product A",
            "description": "Product A",
            "rate": 250.00,
            "quantity": 2.0,
            "unit": "Nos"
        }
    """
    db_items = list(invoice.line_items.all())

    if db_items:
        zoho_items = []
        for li in db_items:
            zoho_items.append({
                'name': li.item_name,
                'description': li.item_name,
                'rate': float(li.rate),
                'quantity': float(li.qty_value),
                'unit': li.qty_unit,
            })
        return zoho_items

    # ---- Fallback for invoices stored before line items were introduced ----
    subtotal = float(invoice.total_amount or 0)
    cgst = float(invoice.cgst or 0)
    sgst = float(invoice.sgst or 0)
    taxable_amount = subtotal - cgst - sgst if subtotal > (cgst + sgst) else subtotal

    return [{
        'description': f'Invoice {invoice.invoice_number}',
        'rate': taxable_amount,
        'quantity': 1,
    }]


# ---------------- USER AUTH ----------------

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        username = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return JsonResponse({'error': 'All fields are required'}, status=400)

        if AppUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        AppUser.objects.create(
            username=username,
            email=email,
            password=hashed.decode('utf-8')
        )

        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')

        return JsonResponse({'token': token, 'name': username, 'email': email}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def signin_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'All fields are required'}, status=400)

        user = _get_user_by_email_or_username(email)
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        token = jwt.encode({
            'email': user.email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')

        return JsonResponse({'token': token, 'email': user.email, 'name': user.username}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def generate_agent_token(request):
    if request.method == 'POST':
        try:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' in content_type:
                data = json.loads(request.body)
                identifier = data.get('username') or data.get('email')
                password = data.get('password')
            else:
                identifier = request.POST.get('username') or request.POST.get('email')
                password = request.POST.get('password')
        except (json.JSONDecodeError, Exception) as e:
            return JsonResponse({'error': f'Bad request body: {str(e)}'}, status=400)

        if not identifier or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        user = _get_user_by_email_or_username(identifier)
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        token = jwt.encode({
            'email': user.email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')

        return JsonResponse({'token': token, 'email': user.email, 'name': user.username}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- ZOHO CONNECTION ----------------

@csrf_exempt
def connect_zoho(request):
    if request.method == 'POST':
        try:
            payload = verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        organization_id = data.get('organization_id')

        if not all([client_id, client_secret, access_token, refresh_token, organization_id]):
            return JsonResponse({'error': 'All Zoho credentials are required'}, status=400)

        # Validate the token against Zoho
        headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
        test_response = req.get('https://www.zohoapis.in/books/v3/organizations', headers=headers)

        if test_response.status_code != 200:
            return JsonResponse({
                'error': 'Invalid Zoho credentials. Please check and try again.',
                'zoho_response': test_response.json()
            }, status=400)

        # Persist credentials linked to this user
        user_email = payload.get('email')
        ZohoConfig.objects.update_or_create(
            user_email=user_email,
            defaults={
                'client_id': client_id,
                'client_secret': client_secret,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'organization_id': organization_id,
            }
        )

        return JsonResponse({'message': 'Zoho Books connected successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- IN-MEMORY STORE (for masters/accounts/items) ----------------

_sync_store = {
    'customers': [],
    'vendors': [],
    'accounts': [],
    'items': [],
}


# ---------------- AGENT DATA RECEIVERS ----------------

@csrf_exempt
def receive_customers(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])
        _sync_store['customers'] = ledgers
        print(f"Received {len(ledgers)} customers")
        return JsonResponse({'status': 'received', 'count': len(ledgers)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_vendors(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])
        _sync_store['vendors'] = ledgers
        print(f"Received {len(ledgers)} vendors")
        return JsonResponse({'status': 'received', 'count': len(ledgers)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_accounts(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        accounts = data.get('accounts', [])
        _sync_store['accounts'] = accounts
        print(f"Received {len(accounts)} accounts")
        return JsonResponse({'status': 'received', 'count': len(accounts)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_items(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        items = data.get('items', [])
        _sync_store['items'] = items
        print(f"Received {len(items)} items")
        return JsonResponse({'status': 'received', 'count': len(items)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_invoices(request):
    """
    Accepts invoices from the Tally agent and persists them along with their line items.

    Expected payload shape:
        {
            "invoices": [
                {
                    "invoice_number": "INV-001",
                    "customer_name": "Acme Corp",
                    "invoice_date": "2024-01-15",
                    "total_amount": "1180.00",
                    "cgst": "90.00",
                    "sgst": "90.00",
                    "line_items": [
                        {
                            "item_name": "Product A",
                            "quantity": "2 Nos",
                            "amount": "1000.00"
                        }
                    ]
                }
            ]
        }
    """
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        invoices = data.get('invoices', [])

        for inv_data in invoices:
            invoice, _ = Invoice.objects.update_or_create(
                invoice_number=inv_data.get('invoice_number', ''),
                defaults={
                    'customer_name': inv_data.get('customer_name', ''),
                    'invoice_date': inv_data.get('invoice_date') or None,
                    'total_amount': str(inv_data.get('total_amount', '0')),
                    'cgst': str(inv_data.get('cgst', '0')),
                    'sgst': str(inv_data.get('sgst', '0')),
                }
            )

            # Save line items if provided
            raw_line_items = inv_data.get('line_items', [])
            if raw_line_items:
                _save_line_items(invoice, raw_line_items)

        print(f"Received {len(invoices)} invoices")
        return JsonResponse({'status': 'received', 'count': len(invoices)}, status=201)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_receipts(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        receipts = data.get('receipts', [])

        for rec in receipts:
            Receipt.objects.update_or_create(
                receipt_number=rec.get('receipt_number', ''),
                defaults={
                    'customer_name': rec.get('customer_name', ''),
                    'receipt_date': rec.get('receipt_date') or None,
                    'amount': str(rec.get('amount', '0')),
                    'payment_mode': rec.get('payment_mode', ''),
                }
            )

        print(f"Received {len(receipts)} receipts")
        return JsonResponse({'status': 'received', 'count': len(receipts)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- DASHBOARD & MIGRATION STATUS ----------------

@csrf_exempt
def data_migration_status(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        customers = len(_sync_store['customers'])
        vendors = len(_sync_store['vendors'])
        coa = len(_sync_store['accounts'])
        items = len(_sync_store['items'])

        total_invoices = Invoice.objects.count()
        migrated_invoices = Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        total_receipts = Receipt.objects.count()
        migrated_receipts = Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        total = customers + vendors + coa + items + total_invoices + total_receipts
        migrated = migrated_invoices + migrated_receipts

        return JsonResponse({
            'fetched_from_tally': total,
            'migrated_to_zoho': migrated,
            'pending_migration_to_zoho': total - migrated,
            'customers': customers,
            'vendors': vendors,
            'COA': coa,
            'items': items,
            'invoices': total_invoices,
            'invoices_migrated': migrated_invoices,
            'receipts': total_receipts,
            'receipts_migrated': migrated_receipts,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def total_records(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        masters = (
            len(_sync_store['customers']) +
            len(_sync_store['vendors']) +
            len(_sync_store['accounts']) +
            len(_sync_store['items'])
        )

        total_invoices = Invoice.objects.count()
        migrated_invoices = Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        total_receipts = Receipt.objects.count()
        migrated_receipts = Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        transactions = total_invoices + total_receipts
        transactions_migrated = migrated_invoices + migrated_receipts

        return JsonResponse({
            'total': masters,
            'migrated': 0,
            'pending': masters,
            'total_trans': transactions,
            'transactions_migrated': transactions_migrated,
            'transactions_pending': transactions - transactions_migrated,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_masters(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        activities = []
        sno = 1

        for c in _sync_store['customers']:
            activities.append({
                'sNo': sno, 'type': 'Customer',
                'name': c.get('name', 'Unknown'),
                'status': 'Fetched', 'lastMigrated': '-'
            })
            sno += 1

        for v in _sync_store['vendors']:
            activities.append({
                'sNo': sno, 'type': 'Vendor',
                'name': v.get('name', 'Unknown'),
                'status': 'Fetched', 'lastMigrated': '-'
            })
            sno += 1

        for a in _sync_store['accounts']:
            activities.append({
                'sNo': sno, 'type': 'Account',
                'name': a.get('account_name', 'Unknown'),
                'status': 'Fetched', 'lastMigrated': '-'
            })
            sno += 1

        for i in _sync_store['items']:
            activities.append({
                'sNo': sno, 'type': 'Item',
                'name': i.get('name', 'Unknown'),
                'status': 'Fetched', 'lastMigrated': '-'
            })
            sno += 1

        return JsonResponse({
            'activities': activities,
            'counts': {
                'customers': len(_sync_store['customers']),
                'vendors': len(_sync_store['vendors']),
                'accounts': len(_sync_store['accounts']),
                'items': len(_sync_store['items']),
            }
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_transactions(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        activities = []
        sno = 1

        for inv in Invoice.objects.all().order_by('-created_at'):
            activities.append({
                'sNo': sno,
                'type': 'Invoice',
                'name': inv.customer_name,
                'status': 'Migrated' if inv.zoho_id else 'Fetched',
                'lastMigrated': str(inv.zoho_migrated_at.date()) if inv.zoho_migrated_at else '-',
                'amount': inv.total_amount,
                'zoho_id': inv.zoho_id or '',
            })
            sno += 1

        for rec in Receipt.objects.all().order_by('-created_at'):
            activities.append({
                'sNo': sno,
                'type': 'Receipt',
                'name': rec.customer_name,
                'status': 'Migrated' if rec.zoho_id else 'Fetched',
                'lastMigrated': str(rec.zoho_migrated_at.date()) if rec.zoho_migrated_at else '-',
                'amount': rec.amount,
                'zoho_id': rec.zoho_id or '',
            })
            sno += 1

        return JsonResponse({
            'activities': activities,
            'counts': {
                'invoices': Invoice.objects.count(),
                'invoices_migrated': Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count(),
                'receipts': Receipt.objects.count(),
                'receipts_migrated': Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count(),
            }
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- PUSH TO ZOHO ----------------

def _push_customers(config, results):
    """Upsert contacts (customers) in Zoho Books — no duplicates."""
    org = config.organization_id
    success, failed = 0, 0

    for c in _sync_store['customers']:
        name = c.get('name', '')
        payload = {
            'contact_name': name,
            'contact_type': 'customer',
            'email': c.get('email', ''),
            'phone': c.get('phone', ''),
            'billing_address': {
                'address': c.get('address', ''),
                'city': c.get('city', ''),
                'state': c.get('state', ''),
                'zip': c.get('pincode', ''),
                'country': c.get('country', 'India'),
            }
        }

        existing_id = _find_existing_contact(name, 'customer', config)
        if existing_id:
            url = f"{ZOHO_BOOKS_BASE}/contacts/{existing_id}?organization_id={org}"
            resp = _zoho_put(url, payload, config)
        else:
            url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}"
            resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            success += 1
        else:
            failed += 1
            print(f"[Customer] Failed: {name} → {resp.text}")

    results['customers'] = {'success': success, 'failed': failed}


def _push_vendors(config, results):
    """Upsert contacts (vendors) in Zoho Books — no duplicates."""
    org = config.organization_id
    success, failed = 0, 0

    for v in _sync_store['vendors']:
        name = v.get('name', '')
        payload = {
            'contact_name': name,
            'contact_type': 'vendor',
            'email': v.get('email', ''),
            'phone': v.get('phone', ''),
            'billing_address': {
                'address': v.get('address', ''),
                'city': v.get('city', ''),
                'state': v.get('state', ''),
                'zip': v.get('pincode', ''),
                'country': v.get('country', 'India'),
            }
        }

        existing_id = _find_existing_contact(name, 'vendor', config)
        if existing_id:
            url = f"{ZOHO_BOOKS_BASE}/contacts/{existing_id}?organization_id={org}"
            resp = _zoho_put(url, payload, config)
        else:
            url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}"
            resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            success += 1
        else:
            failed += 1
            print(f"[Vendor] Failed: {name} → {resp.text}")

    results['vendors'] = {'success': success, 'failed': failed}


def _push_accounts(config, results):
    """Create chart-of-accounts entries in Zoho Books."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}"
    success, failed = 0, 0

    ACCOUNT_TYPE_MAP = {
        'sundry debtors': 'accounts_receivable',
        'sundry creditors': 'accounts_payable',
        'bank accounts': 'bank',
        'cash-in-hand': 'cash',
        'capital account': 'equity',
        'loans (liability)': 'long_term_liability',
        'fixed assets': 'fixed_asset',
        'purchase accounts': 'cost_of_goods_sold',
        'sales accounts': 'income',
        'indirect expenses': 'expense',
        'indirect income': 'other_income',
        'direct expenses': 'cost_of_goods_sold',
    }

    for a in _sync_store['accounts']:
        raw_type = a.get('account_type', '').lower()
        zoho_type = ACCOUNT_TYPE_MAP.get(raw_type, 'expense')

        payload = {
            'account_name': a.get('account_name', ''),
            'account_type': zoho_type,
            'description': a.get('description', ''),
        }
        resp = _zoho_post(url, payload, config)
        if resp.status_code in (200, 201):
            success += 1
        else:
            failed += 1
            print(f"[Account] Failed: {a.get('account_name')} → {resp.text}")

    results['accounts'] = {'success': success, 'failed': failed}


def _push_items(config, results):
    """Create items (products/services) in Zoho Books."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/items?organization_id={org}"
    success, failed = 0, 0

    for i in _sync_store['items']:
        payload = {
            'name': i.get('name', ''),
            'rate': float(i.get('rate') or i.get('price') or 0),
            'description': i.get('description', ''),
            'sku': i.get('sku', ''),
            'unit': i.get('unit', ''),
            'item_type': 'sales_and_purchases',
        }
        if i.get('tax_id'):
            payload['tax_id'] = i['tax_id']

        resp = _zoho_post(url, payload, config)
        if resp.status_code in (200, 201):
            success += 1
        else:
            failed += 1
            print(f"[Item] Failed: {i.get('name')} → {resp.text}")

    results['items'] = {'success': success, 'failed': failed}


def _resolve_customer_id(customer_name, config):
    """
    Look up a Zoho contact ID by display name.
    Returns the contact_id string, or None if not found.
    """
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}&contact_name={customer_name}&contact_type=customer"
    resp = _zoho_get(url, config)
    if resp.status_code == 200:
        contacts = resp.json().get('contacts', [])
        if contacts:
            return contacts[0]['contact_id']
    return None


def _push_invoices(config, results):
    """
    Push invoices to Zoho Books.

    Line items are built from InvoiceLineItem rows (with parsed qty and derived rate).
    Falls back to a single synthetic line item for legacy invoices without stored line items.
    Skips records already migrated (zoho_id set).
    """
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/invoices?organization_id={org}"
    success, failed, skipped = 0, 0, 0

    for inv in Invoice.objects.prefetch_related('line_items').all():
        if inv.zoho_id:
            skipped += 1
            continue

        customer_id = _resolve_customer_id(inv.customer_name, config)
        if not customer_id:
            failed += 1
            print(f"[Invoice] No customer found for: {inv.customer_name}")
            continue

        line_items = _build_zoho_line_items(inv)

        payload = {
            'customer_id': customer_id,
            'invoice_number': inv.invoice_number,
            'date': str(inv.invoice_date) if inv.invoice_date else '',
            'line_items': line_items,
        }

        resp = _zoho_post(url, payload, config)
        if resp.status_code in (200, 201):
            zoho_invoice_id = resp.json().get('invoice', {}).get('invoice_id', '')
            inv.zoho_id = zoho_invoice_id
            inv.zoho_migrated_at = timezone.now()
            inv.save(update_fields=['zoho_id', 'zoho_migrated_at'])
            success += 1
        else:
            failed += 1
            print(f"[Invoice] Failed: {inv.invoice_number} → {resp.text}")

    results['invoices'] = {'success': success, 'failed': failed, 'skipped': skipped}


def _push_receipts(config, results):
    """
    Push receipts to Zoho Books as customer payments.
    Skips records already migrated (zoho_id set).
    """
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/customerpayments?organization_id={org}"
    success, failed, skipped = 0, 0, 0

    PAYMENT_MODE_MAP = {
        'cash': 'cash',
        'cheque': 'check',
        'check': 'check',
        'neft': 'bank_transfer',
        'rtgs': 'bank_transfer',
        'imps': 'bank_transfer',
        'upi': 'bank_transfer',
        'credit card': 'creditcard',
        'debit card': 'creditcard',
    }

    for rec in Receipt.objects.all():
        if rec.zoho_id:
            skipped += 1
            continue

        customer_id = _resolve_customer_id(rec.customer_name, config)
        if not customer_id:
            failed += 1
            print(f"[Receipt] No customer found for: {rec.customer_name}")
            continue

        raw_mode = (rec.payment_mode or '').lower()
        zoho_mode = PAYMENT_MODE_MAP.get(raw_mode, 'cash')

        payload = {
            'customer_id': customer_id,
            'payment_mode': zoho_mode,
            'amount': float(rec.amount or 0),
            'date': str(rec.receipt_date) if rec.receipt_date else '',
            'reference_number': rec.receipt_number,
        }

        resp = _zoho_post(url, payload, config)
        if resp.status_code in (200, 201):
            zoho_payment_id = resp.json().get('payment', {}).get('payment_id', '')
            rec.zoho_id = zoho_payment_id
            rec.zoho_migrated_at = timezone.now()
            rec.save(update_fields=['zoho_id', 'zoho_migrated_at'])
            success += 1
        else:
            failed += 1
            print(f"[Receipt] Failed: {rec.receipt_number} → {resp.text}")

    results['receipts'] = {'success': success, 'failed': failed, 'skipped': skipped}


@csrf_exempt
def push_to_zoho(request):
    if request.method == 'POST':
        try:
            payload = verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        user_email = payload.get('email')

        try:
            config = _get_zoho_config(user_email)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}

        push_types = body.get('types', ['customers', 'vendors', 'accounts', 'items', 'invoices', 'receipts'])

        results = {}
        errors = []

        for push_type, push_fn in [
            ('customers', _push_customers),
            ('vendors', _push_vendors),
            ('accounts', _push_accounts),
            ('items', _push_items),
            ('invoices', _push_invoices),
            ('receipts', _push_receipts),
        ]:
            if push_type in push_types:
                try:
                    push_fn(config, results)
                except Exception as e:
                    errors.append(f"{push_type}: {str(e)}")

        total_success = sum(v.get('success', 0) for v in results.values())
        total_failed = sum(v.get('failed', 0) for v in results.values())
        total_skipped = sum(v.get('skipped', 0) for v in results.values())

        response_data = {
            'message': 'Push to Zoho Books completed.',
            'total_success': total_success,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'details': results,
        }
        if errors:
            response_data['errors'] = errors

        status_code = 200 if not errors and total_failed == 0 else 207
        return JsonResponse(response_data, status=status_code)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- MISC ----------------

@csrf_exempt
def get_next_task(request):
    return JsonResponse({'task': 'fetch_customers'})