from cmath import exp

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from .models import AppUser, Invoice, InvoiceLineItem, Receipt, ZohoConfig, Account, Item, Customer, Vendor, Tax, Purchase, PurchaseLineItem, Payment, CreditNote, VendorCredit, Journal, OpeningBalance, Expense
import json
import jwt
import datetime
import bcrypt
import os
import re
import threading
from decimal import Decimal, InvalidOperation
import requests as req

# ---------------- IN-MEMORY STORE ----------------

_sync_store = {
    'customers': [],
    'vendors': [],
    'accounts': [],
    'items': [],
    'invoices': [],
    'receipts': [],
    'bills': [],
    'payments': [],
    'credit_notes': [],
    'vendor_credits': [],
    'journals': [],
}

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key_here_minimum_32_characters_long")

ZOHO_BOOKS_IN  = "https://www.zohoapis.in/books/v3"     # India domain
ZOHO_BOOKS_COM = "https://www.zohoapis.com/books/v3"    # Global domain
ZOHO_BOOKS_BASE = ZOHO_BOOKS_IN                         # Default — gets overridden per user at runtime


# ---------------- AUTH HELPERS ----------------

def verify_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer ') and not auth_header.startswith('Token '):
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
    try:
        config = ZohoConfig.objects.get(user_email=user_email)
        # Make all push functions use the correct base URL for this org
        global ZOHO_BOOKS_BASE
        ZOHO_BOOKS_BASE = config.api_base_url or ZOHO_BOOKS_IN
        return config
    except ZohoConfig.DoesNotExist:
        raise ValueError('Zoho Books is not connected. Please connect via the settings page.')


def _refresh_zoho_token(config):
    for token_url in [
        'https://accounts.zoho.in/oauth/v2/token',
        'https://accounts.zoho.com/oauth/v2/token',
    ]:
        resp = req.post(
            token_url,
            params={
                'refresh_token': config.refresh_token,
                'client_id':     config.client_id,
                'client_secret': config.client_secret,
                'grant_type':    'refresh_token',
            }
        )
        data = resp.json()
        if 'access_token' in data:
            config.access_token = data['access_token']
            config.save(update_fields=['access_token'])
            return config.access_token

    raise ValueError(f"Failed to refresh Zoho token: {data.get('error', 'Unknown error')}")

def _exchange_zoho_code_for_tokens(client_id, client_secret, code, redirect_uri):
    """
    Custom function: exchanges a one-time Zoho authorization code for
    access_token + refresh_token. Tries India DC first, then Global DC,
    since a client's org may live on either.
    """
    last_error = 'Unknown error'
    for token_url in [
        'https://accounts.zoho.in/oauth/v2/token',
        'https://accounts.zoho.com/oauth/v2/token',
    ]:
        try:
            resp = req.post(
                token_url,
                params={
                    'grant_type':    'authorization_code',
                    'client_id':     client_id,
                    'client_secret': client_secret,
                    'redirect_uri':  redirect_uri,
                    'code':          code,
                },
                timeout=15,
            )
            data = resp.json()
        except req.exceptions.Timeout:
            last_error = 'Request to Zoho timed out.'
            continue
        except Exception as e:
            last_error = str(e)
            continue

        if 'access_token' in data and 'refresh_token' in data:
            return data['access_token'], data['refresh_token']

        last_error = data.get('error', last_error)

    raise ValueError(f"Zoho returned an error: {last_error}. The code may have expired — please try again.")

def _zoho_headers(access_token):
    return {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json',
    }


def _zoho_get(url, config):
    resp = req.get(url, headers=_zoho_headers(config.access_token))
    if resp.status_code == 401:
        _refresh_zoho_token(config)
        resp = req.get(url, headers=_zoho_headers(config.access_token))
    return resp


def _zoho_post(url, payload, config):
    resp = req.post(url, json=payload, headers=_zoho_headers(config.access_token))
    if resp.status_code == 401:
        _refresh_zoho_token(config)
        resp = req.post(url, json=payload, headers=_zoho_headers(config.access_token))
    return resp


def _zoho_put(url, payload, config):
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


def _find_existing_account(name, config):
    """Return account_id if a chart-of-accounts entry with this name already exists in Zoho, else None."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}"
    resp = _zoho_get(url, config)
    if resp.status_code == 200:
        for acct in resp.json().get('chartofaccounts', []):
            if acct.get('account_name', '').strip().lower() == name.strip().lower():
                return acct['account_id']
    return None


def _find_existing_item(name, config):
    """Return item_id if an item with this name already exists in Zoho Books, else None."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/items?organization_id={org}&name={name}"
    resp = _zoho_get(url, config)
    if resp.status_code == 200:
        items = resp.json().get('items', [])
        for item in items:
            if item.get('name', '').strip().lower() == name.strip().lower():
                return item['item_id']
    return None


def _build_zoho_tax_map(config):
    """Returns dict of tax_name.lower() -> tax_id from Zoho Books."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/settings/taxes?organization_id={org}"
    resp = _zoho_get(url, config)
    tax_map = {}
    if resp.status_code == 200:
        for t in resp.json().get('taxes', []):
            tax_map[t.get('tax_name', '').strip().lower()] = t['tax_id']
    return tax_map


def _build_zoho_account_map(config):
    """Returns dict of account_name.lower() -> account_id from Zoho Books."""
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}"
    resp = _zoho_get(url, config)
    account_map = {}
    if resp.status_code == 200:
        for a in resp.json().get('chartofaccounts', []):
            account_map[a.get('account_name', '').strip().lower()] = a['account_id']
    return account_map


# ---------------- LINE ITEM HELPERS ----------------

def _parse_quantity(raw_qty):
    raw = (raw_qty or '').strip()
    if not raw:
        return Decimal('1'), 'Nos'
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
    try:
        amount_d = Decimal(str(amount))
        qty_d = Decimal(str(qty_value))
        if qty_d == 0:
            return amount_d
        return (amount_d / qty_d).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError):
        return Decimal('0')


def _save_line_items(invoice, raw_line_items):
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
            qty_value=qty_value,
            qty_unit=qty_unit,
            amount=amount,
            rate=rate,
        ))
    if items_to_create:
        InvoiceLineItem.objects.bulk_create(items_to_create)


def _build_zoho_line_items(invoice):
    db_items = list(invoice.line_items.all())
    if db_items:
        return [{
            'name': li.item_name,
            'description': li.item_name,
            'rate': float(li.rate),
            'quantity': float(li.qty_value),
            'unit': li.qty_unit,
        } for li in db_items]

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
        AppUser.objects.create(username=username, email=email, password=hashed.decode('utf-8'))

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

        # Try India domain first, then Global — store whichever works
        connected_base = None
        test_response = None
        for base in [ZOHO_BOOKS_IN, ZOHO_BOOKS_COM]:
            test_response = req.get(
                f'{base}/organizations',
                headers={'Authorization': f'Zoho-oauthtoken {access_token}'}
            )
            if test_response.status_code == 200:
                connected_base = base
                break

        if not connected_base:
            return JsonResponse({
                'error': 'Invalid Zoho credentials. Please check and try again.',
                'zoho_response': test_response.json()
            }, status=400)

        user_email = payload.get('email')
        ZohoConfig.objects.update_or_create(
            user_email=user_email,
            defaults={
                'client_id':       client_id,
                'client_secret':   client_secret,
                'access_token':    access_token,
                'refresh_token':   refresh_token,
                'organization_id': organization_id,
                'api_base_url':    connected_base,   # ← persists IN vs COM
            }
        )

        return JsonResponse({'message': 'Zoho Books connected successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- AGENT DATA RECEIVERS ----------------

@csrf_exempt
def receive_customers(request):
    """
    Persist customers to DB (Customer model) AND keep in memory.
    Previously only stored in memory — lost on server restart.
    """
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])

        for c in ledgers:
            name = (c.get('name', '') or '').strip()
            if not name:
                continue
            try:
                Customer.objects.update_or_create(
                    name=name,
                    defaults={
                        'email':   c.get('email', '') or None,
                        'phone':   c.get('ledger_mobile', '') or None,
                        'address': c.get('address', '') or None,
                        'state':   c.get('state_name', '') or None,
                        'pincode': c.get('pincode', '') or None,
                        'country': c.get('country_name', '') or 'India',
                    }
                )
            except Exception as e:
                print(f"⚠️ Customer save error for '{name}': {e}")

        _sync_store['customers'] = ledgers
        print(f"Received {len(ledgers)} customers")
        return JsonResponse({'status': 'received', 'count': len(ledgers)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_vendors(request):
    """
    Persist vendors to DB (Vendor model) AND keep in memory.
    Previously only stored in memory — lost on server restart.
    """
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])

        for v in ledgers:
            name = (v.get('name', '') or '').strip()
            if not name:
                continue
            try:
                Vendor.objects.update_or_create(
                    name=name,
                    defaults={
                        'email':   v.get('email', '') or None,
                        'phone':   v.get('ledger_mobile', '') or None,
                        'address': v.get('address', '') or None,
                        'state':   v.get('state_name', '') or None,
                        'pincode': v.get('pincode', '') or None,
                        'country': v.get('country_name', '') or 'India',
                    }
                )
            except Exception as e:
                print(f"⚠️ Vendor save error for '{name}': {e}")

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

        for a in accounts:
            Account.objects.update_or_create(
                account_name=a.get('account_name', ''),
                defaults={
                    'account_code': a.get('account_code', ''),
                    'account_type': a.get('account_type'),
                }
            )

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

        for i in items:
            name = (i.get('name', '') or '').strip()
            if not name or name.lower() == 'unknown':
                continue
            Item.objects.update_or_create(
                name=i.get('name', ''),
                defaults={
                    'rate':           str(i.get('rate', '0')),
                    'description':    i.get('description', ''),
                    'sku':            i.get('sku', ''),
                    'product_type':   i.get('product_type', ''),
                    'type_of_supply': i.get('type_of_supply', 'Unknown'),
                    'gst_applicable': i.get('gst_applicable', ''),
                    'gst_rate':       str(i.get('gst_rate', '0')),
                    'hsn_code':       i.get('hsn_code', ''),
                }
            )

        _sync_store['items'] = items
        print(f"Received {len(items)} items")
        return JsonResponse({'status': 'received', 'count': len(items)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_invoices(request):
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
                    'invoice_date':  inv_data.get('invoice_date') or None,
                    'total_amount':  str(inv_data.get('total_amount', '0')),
                    'cgst':          str(inv_data.get('cgst', '0')),
                    'sgst':          str(inv_data.get('sgst', '0')),
                }
            )

            raw_line_items = inv_data.get('line_items') or inv_data.get('items') or []
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
                    'receipt_date':  rec.get('receipt_date') or None,
                    'amount':        str(rec.get('amount', '0')),
                    'payment_mode':  rec.get('payment_mode', ''),
                }
            )

        print(f"Received {len(receipts)} receipts")
        return JsonResponse({'status': 'received', 'count': len(receipts)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_purchases(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        bills = data.get('bills', [])
        _sync_store['bills'] = bills
        from datetime import datetime
        saved = 0
        for b in bills:
            try:
                date = datetime.strptime(b['bill_date'], '%Y-%m-%d').date() if b.get('bill_date') else None
                purchase, _ = Purchase.objects.update_or_create(
                    bill_number=b['bill_number'],
                    defaults={
                        'vendor_name':  b.get('vendor_name', ''),
                        'bill_date':    date,
                        'amount':       str(b.get('total_amount', '0')),
                        'total_amount': b.get('total_amount', '0'),
                        'cgst':         str(b.get('cgst', '0')),
                        'sgst':         str(b.get('sgst', '0')),
                        'igst':         str(b.get('igst', '0')),
                    }
                )
                raw_lines = b.get('line_items', [])
                if raw_lines:
                    purchase.line_items.all().delete()
                    items_to_create = []
                    for li in raw_lines:
                        try:
                            amt = Decimal(str(li.get('amount', '0')))
                        except InvalidOperation:
                            amt = Decimal('0')
                        qty_raw = (li.get('quantity') or '1').strip()
                        qty_match = re.match(r'^(\d+(?:\.\d+)?)', qty_raw)
                        qty = Decimal(qty_match.group(1)) if qty_match else Decimal('1')
                        rate = (amt / qty).quantize(Decimal('0.01')) if qty > 0 else amt
                        items_to_create.append(PurchaseLineItem(
                            purchase=purchase,
                            item_name=li.get('item_name', ''),
                            quantity=qty_raw,
                            amount=amt,
                            rate=rate,
                        ))
                    if items_to_create:
                        PurchaseLineItem.objects.bulk_create(items_to_create)
                saved += 1
            except Exception as e:
                print(f"⚠️ Bill save error: {e}")
        print(f"Received {len(bills)} bills, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(bills)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_payments(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        payments = data.get('payments', [])
        _sync_store['payments'] = payments
        from datetime import datetime
        saved = 0
        for p in payments:
            try:
                date = datetime.strptime(p['payment_date'], '%Y-%m-%d').date() if p.get('payment_date') else None
                Payment.objects.update_or_create(
                    payment_number=p['payment_number'],
                    defaults={
                        'vendor_name':  p.get('vendor_name', ''),
                        'payment_date': date,
                        'amount':       p.get('amount', '0'),
                        'payment_mode': p.get('payment_mode', ''),
                    }
                )
                saved += 1
            except Exception as e:
                print(f"⚠️ Payment save error: {e}")
        print(f"Received {len(payments)} payments, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(payments)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_credit_notes(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        credit_notes = data.get('credit_notes', [])
        _sync_store['credit_notes'] = credit_notes
        from datetime import datetime
        saved = 0
        for c in credit_notes:
            try:
                date = datetime.strptime(c['credit_note_date'], '%Y-%m-%d').date() if c.get('credit_note_date') else None
                CreditNote.objects.update_or_create(
                    credit_note_number=c['credit_note_number'],
                    defaults={
                        'customer_name':    c.get('customer_name', ''),
                        'credit_note_date': date,
                        'amount':           str(c.get('total_amount', '0')),
                        'total_amount':     str(c.get('total_amount', '0')),
                        'cgst':             str(c.get('cgst', '0')),
                        'sgst':             str(c.get('sgst', '0')),
                        'igst':             str(c.get('igst', '0')),
                    }
                )
                saved += 1
            except Exception as e:
                print(f"⚠️ Credit note save error: {e}")
        print(f"Received {len(credit_notes)} credit notes, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(credit_notes)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_vendor_credits(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        vendor_credits = data.get('vendor_credits', [])
        _sync_store['vendor_credits'] = vendor_credits
        from datetime import datetime
        saved = 0
        for v in vendor_credits:
            try:
                date = datetime.strptime(v['vendor_credit_date'], '%Y-%m-%d').date() if v.get('vendor_credit_date') else None
                VendorCredit.objects.update_or_create(
                    vendor_credit_number=v['vendor_credit_number'],
                    defaults={
                        'vendor_name':        v.get('vendor_name', ''),
                        'vendor_credit_date': date,
                        'total_amount':       str(v.get('total_amount', '0')),
                        'cgst':               str(v.get('cgst', '0')),
                        'sgst':               str(v.get('sgst', '0')),
                    }
                )
                saved += 1
            except Exception as e:
                print(f"⚠️ Vendor credit save error: {e}")
        print(f"Received {len(vendor_credits)} vendor credits, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(vendor_credits)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_journals(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        journals = data.get('journals', [])
        from datetime import datetime
        from .models import JournalLine
        saved = 0
        for j in journals:
            try:
                date = datetime.strptime(j['journal_date'], '%Y-%m-%d').date() if j.get('journal_date') else None
                journal_obj, _ = Journal.objects.update_or_create(
                    voucher_number=j['journal_number'],
                    defaults={
                        'voucher_date': date,
                        'narration':    j.get('narration', ''),
                        'amount':       j.get('total_amount', '0'),
                    }
                )
                lines = j.get('lines', [])
                if lines:
                    JournalLine.objects.filter(journal=journal_obj).delete()
                    for line in lines:
                        JournalLine.objects.create(
                            journal=journal_obj,
                            account_name=line.get('account_name', ''),
                            debit=line.get('debit', '0'),
                            credit=line.get('credit', '0'),
                        )
                saved += 1
            except Exception as e:
                print(f"⚠️ Journal save error: {e}")
        print(f"Received {len(journals)} journals, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(journals)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_expenses(request):
    """
    Receives expense entries from the agent.
    These are Payment vouchers in Tally where the debit side is an
    expense account (not a vendor/sundry creditor).
    """
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        expenses = data.get('expenses', [])
        from datetime import datetime
        saved = 0
        for e in expenses:
            try:
                date = datetime.strptime(e['payment_date'], '%Y-%m-%d').date() if e.get('payment_date') else None
                Expense.objects.update_or_create(
                    payment_number=e.get('payment_number', ''),
                    defaults={
                        'payment_date': date,
                        'account_name': e.get('account_name', ''),
                        'paid_through': e.get('paid_through', 'Cash'),
                        'amount':       e.get('amount', '0'),
                        'narration':    e.get('narration', ''),
                    }
                )
                saved += 1
            except Exception as ex:
                print(f"⚠️ Expense save error: {ex}")
        print(f"Received {len(expenses)} expenses, saved {saved} to DB")
        return JsonResponse({'status': 'received', 'count': len(expenses)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- DASHBOARD & MIGRATION STATUS ----------------

@csrf_exempt
def data_migration_status(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        customers = Customer.objects.count()
        vendors = Vendor.objects.count()
        coa = Account.objects.count()
        items = Item.objects.count()

        total_invoices = Invoice.objects.count()
        migrated_invoices = Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        total_receipts = Receipt.objects.count()
        migrated_receipts = Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        migrated_accounts = Account.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_items = Item.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        migrated_customers = Customer.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_vendors = Vendor.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_payments = Payment.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_bills = Purchase.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_credit_notes = CreditNote.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_vendor_credits = VendorCredit.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_journals = Journal.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        total = (customers + vendors + coa + items + total_invoices + total_receipts
                 + Purchase.objects.count() + Payment.objects.count()
                 + CreditNote.objects.count() + VendorCredit.objects.count() + Journal.objects.count())
        migrated = (migrated_invoices + migrated_receipts + migrated_accounts + migrated_items
                    + migrated_customers + migrated_vendors + migrated_payments + migrated_bills
                    + migrated_credit_notes + migrated_vendor_credits + migrated_journals)

        return JsonResponse({
            'fetched_from_tally':      total,
            'migrated_to_zoho':        migrated,
            'pending_migration_to_zoho': total - migrated,
            'customers':               customers,
            'vendors':                 vendors,
            'COA':                     coa,
            'items':                   items,
            'invoices':                total_invoices,
            'invoices_migrated':       migrated_invoices,
            'receipts':                total_receipts,
            'receipts_migrated':       migrated_receipts,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def total_records(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        migrated_customers = Customer.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_vendors = Vendor.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_accounts = Account.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_items = Item.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        migrated_taxes = Tax.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()

        master_count = (
            Customer.objects.count() + Vendor.objects.count() +
            Account.objects.count() + Item.objects.count() + Tax.objects.count()
        )
        migrated_masters = (
            migrated_customers + migrated_vendors +
            migrated_accounts + migrated_items + migrated_taxes
        )

        total_trans = (
            Invoice.objects.count() + Receipt.objects.count() +
            Purchase.objects.count() + Payment.objects.count() +
            CreditNote.objects.count() + VendorCredit.objects.count() +
            Journal.objects.count() + Expense.objects.count() +
            OpeningBalance.objects.count()
        )
        migrated_trans = (
            Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            Purchase.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            Payment.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            CreditNote.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            VendorCredit.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            Journal.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            Expense.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count() +
            OpeningBalance.objects.filter(is_pushed=True).count()
        )

        return JsonResponse({
            'total':                  master_count,
            'migrated':               migrated_masters,
            'pending':                master_count - migrated_masters,
            'total_trans':            total_trans,
            'transactions_migrated':  migrated_trans,
            'transactions_pending':   total_trans - migrated_trans,
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

        for c in Customer.objects.all():
            activities.append({
                'sNo': sno, 'type': 'Customer',
                'name': c.name,
                'status': 'Migrated' if c.zoho_id else 'Fetched',
                'lastMigrated': str(c.zoho_migrated_at.date()) if c.zoho_migrated_at else '-'
            })
            sno += 1

        for v in Vendor.objects.all():
            activities.append({
                'sNo': sno, 'type': 'Vendor',
                'name': v.name,
                'status': 'Migrated' if v.zoho_id else 'Fetched',
                'lastMigrated': str(v.zoho_migrated_at.date()) if v.zoho_migrated_at else '-'
            })
            sno += 1

        for a in Account.objects.all():
            activities.append({
                'sNo': sno, 'type': 'Account',
                'name': a.account_name,
                'status': 'Migrated' if a.zoho_id else 'Fetched',
                'lastMigrated': str(a.zoho_migrated_at.date()) if a.zoho_migrated_at else '-'
            })
            sno += 1

        for i in Item.objects.all():
            activities.append({
                'sNo': sno, 'type': 'Item',
                'name': i.name,
                'status': 'Migrated' if i.zoho_id else 'Fetched',
                'lastMigrated': str(i.zoho_migrated_at.date()) if i.zoho_migrated_at else '-'
            })
            sno += 1

        return JsonResponse({
            'activities': activities,
            'counts': {
                'customers': Customer.objects.count(),
                'vendors':   Vendor.objects.count(),
                'accounts':  Account.objects.count(),
                'items':     Item.objects.count(),
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
                'sNo': sno, 'type': 'Invoice',
                'name': inv.customer_name,
                'status': 'Migrated' if inv.zoho_id else 'Fetched',
                'lastMigrated': str(inv.zoho_migrated_at.date()) if inv.zoho_migrated_at else '-',
                'amount': inv.total_amount,
            })
            sno += 1

        for rec in Receipt.objects.all().order_by('-created_at'):
            activities.append({
                'sNo': sno, 'type': 'Receipt',
                'name': rec.customer_name,
                'status': 'Migrated' if rec.zoho_id else 'Fetched',
                'lastMigrated': str(rec.zoho_migrated_at.date()) if rec.zoho_migrated_at else '-',
                'amount': rec.amount,
            })
            sno += 1

        for b in Purchase.objects.all().order_by('-id'):
            activities.append({
                'sNo': sno, 'type': 'Bill',
                'name': b.vendor_name,
                'status': 'Migrated' if b.zoho_id else 'Fetched',
                'lastMigrated': str(b.zoho_migrated_at.date()) if b.zoho_migrated_at else '-',
                'amount': b.amount,
            })
            sno += 1

        for p in Payment.objects.all().order_by('-id'):
            activities.append({
                'sNo': sno, 'type': 'Payment Made',
                'name': p.vendor_name,
                'status': 'Migrated' if p.zoho_id else 'Fetched',
                'lastMigrated': str(p.zoho_migrated_at.date()) if p.zoho_migrated_at else '-',
                'amount': p.amount,
            })
            sno += 1

        for c in CreditNote.objects.all().order_by('-id'):
            activities.append({
                'sNo': sno, 'type': 'Credit Note',
                'name': c.customer_name,
                'status': 'Migrated' if c.zoho_id else 'Fetched',
                'lastMigrated': str(c.zoho_migrated_at.date()) if c.zoho_migrated_at else '-',
                'amount': c.amount,
            })
            sno += 1

        for v in VendorCredit.objects.all().order_by('-id'):
            activities.append({
                'sNo': sno, 'type': 'Vendor Credit',
                'name': v.vendor_name,
                'status': 'Migrated' if v.zoho_id else 'Fetched',
                'lastMigrated': str(v.zoho_migrated_at.date()) if v.zoho_migrated_at else '-',
                'amount': v.amount,
            })
            sno += 1

        for j in Journal.objects.all().order_by('-id'):
            display_narration = j.narration.split('__lines__')[0] if '__lines__' in (j.narration or '') else j.narration
            activities.append({
                'sNo': sno, 'type': 'Journal',
                'name': display_narration or f'Journal {j.voucher_number}',
                'status': 'Migrated' if j.zoho_id else 'Fetched',
                'lastMigrated': str(j.zoho_migrated_at.date()) if j.zoho_migrated_at else '-',
                'amount': j.amount,
            })
            sno += 1

        return JsonResponse({
            'activities': activities,
            'counts': {
                'invoices':       Invoice.objects.count(),
                'receipts':       Receipt.objects.count(),
                'bills':          Purchase.objects.count(),
                'payments':       Payment.objects.count(),
                'credit_notes':   CreditNote.objects.count(),
                'vendor_credits': VendorCredit.objects.count(),
                'journals':       Journal.objects.count(),
            }
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- PUSH TO ZOHO ----------------

def _push_customers(config, results):
    """Upsert contacts (customers) in Zoho Books — reads from DB."""
    org = config.organization_id
    success, failed = 0, 0

    for c in Customer.objects.all():
        if c.zoho_id:
            continue
        name = c.name
        payload = {
            'contact_name': name,
            'contact_type': 'customer',
            'email':        c.email or '',
            'phone':        c.phone or '',
            'billing_address': {
                'address': c.address or '',
                'state':   c.state or '',
                'zip':     c.pincode or '',
                'country': c.country or 'India',
            }
        }

        existing_id = _find_existing_contact(name, 'customer', config)
        if existing_id:
            url = f"{ZOHO_BOOKS_BASE}/contacts/{existing_id}?organization_id={org}"
            resp = _zoho_put(url, payload, config)
            if resp.status_code in (200, 201):
                c.mark_migrated(existing_id)
                success += 1
        else:
            url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}"
            resp = _zoho_post(url, payload, config)
            if resp.status_code in (200, 201):
                c.mark_migrated(resp.json().get('contact', {}).get('contact_id', ''))
                success += 1
            else:
                failed += 1
                print(f"[Customer] Failed: {name} → {resp.text}")

    results['customers'] = {'success': success, 'failed': failed}
    print(f"{'='*50}")
    print(f"✅ CUSTOMERS pushed → success: {success} | failed: {failed}")
    print(f"{'='*50}")


def _push_vendors(config, results):
    """Upsert contacts (vendors) in Zoho Books — reads from DB."""
    org = config.organization_id
    success, failed = 0, 0

    for v in Vendor.objects.all():
        if v.zoho_id:
            continue
        name = v.name
        payload = {
            'contact_name': name,
            'contact_type': 'vendor',
            'email':        v.email or '',
            'phone':        v.phone or '',
            'billing_address': {
                'address': v.address or '',
                'state':   v.state or '',
                'zip':     v.pincode or '',
                'country': v.country or 'India',
            }
        }

        existing_id = _find_existing_contact(name, 'vendor', config)
        if existing_id:
            url = f"{ZOHO_BOOKS_BASE}/contacts/{existing_id}?organization_id={org}"
            resp = _zoho_put(url, payload, config)
            if resp.status_code in (200, 201):
                v.mark_migrated(existing_id)
                success += 1
        else:
            url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}"
            resp = _zoho_post(url, payload, config)
            if resp.status_code in (200, 201):
                v.mark_migrated(resp.json().get('contact', {}).get('contact_id', ''))
                success += 1
            else:
                failed += 1
                print(f"[Vendor] Failed: {name} → {resp.text}")

    results['vendors'] = {'success': success, 'failed': failed}
    print(f"{'='*50}")
    print(f"✅ VENDORS pushed → success: {success} | failed: {failed}")
    print(f"{'='*50}")


# Unified account type map — single source of truth
ACCOUNT_TYPE_MAP = {
    'sundry debtors':           'accounts_receivable',
    'sundry creditors':         'accounts_payable',
    'bank accounts':            'bank',
    'bank occ a/c':             'bank',
    'bank od a/c':              'bank',
    'cash-in-hand':             'cash',
    'capital account':          'equity',
    'reserves & surplus':       'equity',
    'loans (liability)':        'long_term_liability',
    'secured loans':            'other_liability',
    'unsecured loans':          'long_term_liability',
    'fixed assets':             'fixed_asset',
    'purchase accounts':        'cost_of_goods_sold',
    'stock-in-hand':            'cost_of_goods_sold',
    'sales accounts':           'income',
    'direct incomes':           'income',
    'indirect incomes':         'other_income',
    'direct expenses':          'expense',
    'indirect expenses':        'other_expense',
    'current assets':           'other_current_asset',
    'current liabilities':      'other_current_liability',
    'duties & taxes':           'other_current_liability',
    'provisions':               'other_current_liability',
    'deposits (asset)':         'other_current_asset',
    'loans & advances (asset)': 'other_current_asset',
    'investments':              'other_current_asset',
    'misc. expenses (asset)':   'other_asset',
    'branch / divisions':       'other_liability',
    'suspense a/c':             'other_liability',
    'retained earnings':        'income',
}


def _push_accounts(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    for account in Account.objects.all():
        if account.zoho_id:
            skipped += 1
            continue

        raw_type = (account.account_type or '').lower()
        zoho_type = ACCOUNT_TYPE_MAP.get(raw_type, 'expense')

        payload = {
            'account_name': account.account_name,
            'account_type': zoho_type,
        }

        existing_id = _find_existing_account(account.account_name, config)
        if existing_id:
            account.mark_migrated(existing_id)
            skipped += 1
            continue

        url = f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}"
        resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            zoho_account_id = resp.json().get('chart_of_account', {}).get('account_id', '')
            account.mark_migrated(zoho_account_id)
            success += 1
        else:
            failed += 1
            print(f"[Account] Failed: {account.account_name} → {resp.text}")

    results['accounts'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ ACCOUNTS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_items(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    for item in Item.objects.all():
        if item.zoho_id:
            skipped += 1
            continue

        existing_id = _find_existing_item(item.name, config)
        if existing_id:
            item.mark_migrated(existing_id)
            skipped += 1
            continue

        try:
            rate = float(item.rate or 0)
        except (ValueError, TypeError):
            rate = 0.0

        payload = {
            'name':        item.name,
            'rate':        rate,
            'description': item.description or '',
            'sku':         item.sku or '',
            'unit':        item.product_type or '',
            'item_type':   'sales_and_purchases',
        }

        url = f"{ZOHO_BOOKS_BASE}/items?organization_id={org}"
        resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            zoho_item_id = resp.json().get('item', {}).get('item_id', '')
            item.mark_migrated(zoho_item_id)
            success += 1
        else:
            failed += 1
            print(f"[Item] Failed: {item.name} → {resp.text}")

    results['items'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ ITEMS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_taxes(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    check_resp = _zoho_get(f"{ZOHO_BOOKS_BASE}/settings/taxes?organization_id={org}", config)
    existing_tax_map = {}
    if check_resp.status_code == 200:
        for t in check_resp.json().get('taxes', []):
            existing_tax_map[t.get('tax_name', '').strip().lower()] = t['tax_id']

    for tax in Tax.objects.all():
        if tax.zoho_id:
            skipped += 1
            continue

        match_id = existing_tax_map.get(tax.tax_name.strip().lower())
        if match_id:
            tax.mark_migrated(match_id)
            skipped += 1
            continue

        payload = {
            'tax_name':       tax.tax_name,
            'tax_percentage': float(tax.tax_rate or 0),
            'tax_type':       'tax',
            'is_active':      tax.is_active,
        }
        url = f"{ZOHO_BOOKS_BASE}/settings/taxes?organization_id={org}"
        resp = _zoho_post(url, payload, config)
        if resp.status_code in (200, 201):
            zoho_tax_id = resp.json().get('tax', {}).get('tax_id', '')
            tax.mark_migrated(zoho_tax_id)
            success += 1
        else:
            failed += 1
            print(f"[Tax] Failed: {tax.tax_name} → {resp.text}")

    results['taxes'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ TAXES pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _resolve_customer_id(customer_name, config):
    db_customer = Customer.objects.filter(name=customer_name).first()
    if db_customer and db_customer.zoho_id:
        return db_customer.zoho_id

    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}&contact_name={customer_name}&contact_type=customer"
    resp = _zoho_get(url, config)
    if resp.status_code == 200:
        contacts = resp.json().get('contacts', [])
        if contacts:
            zoho_id = contacts[0]['contact_id']
            if db_customer:
                db_customer.zoho_id = zoho_id
                db_customer.save(update_fields=['zoho_id'])
            return zoho_id
    return None


def _resolve_vendor_id(vendor_name, config):
    db_vendor = Vendor.objects.filter(name=vendor_name).first()
    if db_vendor and db_vendor.zoho_id:
        return db_vendor.zoho_id
    return _find_existing_contact(vendor_name, 'vendor', config)


def _get_zoho_account_id(account_type, config):
    org = config.organization_id
    resp = _zoho_get(
        f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type={account_type}",
        config
    )
    if resp.status_code == 200:
        accounts = resp.json().get('chartofaccounts', [])
        if accounts:
            print(f"[Account] Found {account_type}: {accounts[0]['account_name']} → {accounts[0]['account_id']}")
            return accounts[0]['account_id']
    return None


def _push_invoices(config, results):
    """
    Push invoices to Zoho Books.
    Line items are linked to a Sales/Income account so they appear
    correctly in the Trial Balance under Income.
    """
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    sales_account_id = _get_zoho_account_id('income', config)
    print(f"[Invoice] sales_account_id = {sales_account_id}")

    for inv in Invoice.objects.prefetch_related('line_items').all():
        if inv.zoho_id:
            skipped += 1
            continue

        customer_id = _resolve_customer_id(inv.customer_name, config)
        if not customer_id:
            if inv.customer_name == "Cash Customer":
                resp_c = _zoho_post(
                    f"{ZOHO_BOOKS_BASE}/contacts?organization_id={org}",
                    {'contact_name': 'Cash Customer', 'contact_type': 'customer'},
                    config
                )
                if resp_c.status_code in (200, 201):
                    customer_id = resp_c.json().get('contact', {}).get('contact_id', '')
                    Customer.objects.update_or_create(
                        name='Cash Customer',
                        defaults={'zoho_id': customer_id}
                    )
            if not customer_id:
                failed += 1
                print(f"[Invoice] No customer found for: {inv.customer_name}")
                continue

        db_items = list(inv.line_items.all())
        if db_items:
            line_items = []
            for li in db_items:
                item = {
                    'name':        li.item_name,
                    'description': li.item_name,
                    'rate':        float(li.rate),
                    'quantity':    float(li.qty_value),
                    'unit':        li.qty_unit,
                }
                if sales_account_id:
                    item['account_id'] = sales_account_id
                line_items.append(item)
        else:
            subtotal = float(inv.total_amount or 0)
            cgst = float(inv.cgst or 0)
            sgst = float(inv.sgst or 0)
            taxable = subtotal - cgst - sgst if subtotal > (cgst + sgst) else subtotal
            item = {
                'description': f'Invoice {inv.invoice_number}',
                'rate':        taxable,
                'quantity':    1,
            }
            if sales_account_id:
                item['account_id'] = sales_account_id
            line_items = [item]

        payload = {
            'customer_id':    customer_id,
            'invoice_number': inv.invoice_number,
            'date':           str(inv.invoice_date) if inv.invoice_date else '',
            'line_items':     line_items,
        }

        resp = _zoho_post(f"{ZOHO_BOOKS_BASE}/invoices?organization_id={org}", payload, config)
        if resp.status_code in (200, 201):
            inv.zoho_id = resp.json().get('invoice', {}).get('invoice_id', '')
            inv.zoho_migrated_at = timezone.now()
            inv.save(update_fields=['zoho_id', 'zoho_migrated_at'])
            success += 1
        else:
            failed += 1
            error_msg = resp.json().get('message', resp.text[:200])
            print(f"[Invoice] Failed: {inv.invoice_number} | Customer: {inv.customer_name} | Reason: {error_msg}")

    results['invoices'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ INVOICES pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_receipts(config, results):
    org = config.organization_id
    url = f"{ZOHO_BOOKS_BASE}/customerpayments?organization_id={org}"
    success, failed, skipped = 0, 0, 0

    PAYMENT_MODE_MAP = {
        'cash':        'cash',
        'cheque':      'check',
        'check':       'check',
        'neft':        'bank_transfer',
        'rtgs':        'bank_transfer',
        'imps':        'bank_transfer',
        'upi':         'bank_transfer',
        'credit card': 'creditcard',
        'debit card':  'creditcard',
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
        zoho_mode = next(
            (v for k, v in PAYMENT_MODE_MAP.items() if k in raw_mode),
            'cash'
        )

        payload = {
            'customer_id':      customer_id,
            'payment_mode':     zoho_mode,
            'amount':           float(rec.amount or 0),
            'date':             str(rec.receipt_date) if rec.receipt_date else '',
            'reference_number': rec.receipt_number,
        }

        resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            zoho_payment_id = resp.json().get('payment', {}).get('payment_id', '')
            rec.mark_migrated(zoho_payment_id)
            success += 1
        else:
            failed += 1
            error_msg = resp.json().get('message', resp.text[:200])
            print(f"[Receipt] Failed: {rec.receipt_number} | Customer: {rec.customer_name} | Reason: {error_msg}")

    results['receipts'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ RECEIPTS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_bills(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    purchase_account_id = None
    for acct_type in ['cost_of_goods_sold', 'expense']:
        acct_resp = _zoho_get(
            f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type={acct_type}",
            config
        )
        if acct_resp.status_code == 200:
            accounts = acct_resp.json().get('chartofaccounts', [])
            if accounts:
                purchase_account_id = accounts[0]['account_id']
                break

    for b in Purchase.objects.all():
        if b.zoho_id:
            skipped += 1
            continue

        vendor_id = _resolve_vendor_id(b.vendor_name, config)
        if not vendor_id:
            failed += 1
            print(f"[Bill] No vendor found for: {b.vendor_name}")
            continue

        line_item = {
            'description': f'Bill {b.bill_number}',
            'rate':        float(b.amount or 0),
            'quantity':    1,
        }
        if purchase_account_id:
            line_item['account_id'] = purchase_account_id

        payload = {
            'vendor_id':   vendor_id,
            'bill_number': str(b.bill_number) if b.bill_number else '',
            'date':        str(b.bill_date) if b.bill_date else '',
            'line_items':  [line_item],
        }

        resp = _zoho_post(f"{ZOHO_BOOKS_BASE}/bills?organization_id={org}", payload, config)
        if resp.status_code in (200, 201):
            b.mark_migrated(resp.json().get('bill', {}).get('bill_id', ''))
            success += 1
        else:
            failed += 1
            print(f"[Bill] Failed: {b.bill_number} → {resp.text}")

    results['bills'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ BILLS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_payments(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0
    import time
    print(f"[Payment] Starting push, total records: {Payment.objects.count()}")

    for p in Payment.objects.all():
        if p.zoho_id:
            skipped += 1
            continue

        skip_keywords = ['bank', 'cash', 'city union', 'hdfc', 'sbi', 'icici', 'axis', 'canara', 'kotak']
        if any(k in (p.vendor_name or '').lower() for k in skip_keywords):
            print(f"[Payment] Skipping bank/cash entry: {p.vendor_name}")
            skipped += 1
            continue

        vendor_id = _find_existing_contact(p.vendor_name, 'vendor', config)
        if not vendor_id:
            failed += 1
            print(f"[Payment] No vendor found for: {p.vendor_name}")
            continue

        payload = {
            'vendor_id':        vendor_id,
            'payment_mode':     'cash',
            'amount':           float(p.amount or 0),
            'date':             str(p.payment_date) if p.payment_date else '',
            'reference_number': p.payment_number,
        }

        resp = _zoho_post(
            f"{ZOHO_BOOKS_BASE}/vendorpayments?organization_id={org}",
            payload, config
        )
        if resp.status_code in (200, 201):
            resp_data = resp.json()
            payment_id = (
                resp_data.get('vendorpayment', {}).get('payment_id') or
                resp_data.get('payment', {}).get('payment_id') or
                ''
            )
            Payment.objects.filter(pk=p.pk).update(
                zoho_id=payment_id,
                zoho_migrated_at=timezone.now()
            )
            success += 1
        else:
            failed += 1
            print(f"[Payment] Failed: {p.payment_number} → {resp.text[:200]}")

        time.sleep(0.7)

    results['payments'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ PAYMENTS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_credit_notes(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    for c in CreditNote.objects.all():
        if c.zoho_id:
            skipped += 1
            continue

        customer_id = _resolve_customer_id(c.customer_name, config)
        if not customer_id:
            failed += 1
            continue

        payload = {
            'customer_id': customer_id,
            'date':        str(c.credit_note_date) if c.credit_note_date else '',
            'line_items':  [{'description': f'Credit Note {c.credit_note_number}', 'rate': float(c.amount or 0), 'quantity': 1}],
        }
        resp = _zoho_post(f"{ZOHO_BOOKS_BASE}/creditnotes?organization_id={org}", payload, config)
        if resp.status_code in (200, 201):
            c.mark_migrated(resp.json().get('creditnote', {}).get('creditnote_id', ''))
            success += 1
        else:
            failed += 1
            print(f"[CreditNote] Failed: {c.credit_note_number} → {resp.text}")

    results['credit_notes'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ CREDIT NOTES pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_vendor_credits(config, results):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    acct_resp = _zoho_get(f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type=expense", config)
    fallback_account_id = ''
    if acct_resp.status_code == 200:
        accounts = acct_resp.json().get('chartofaccounts', [])
        if accounts:
            fallback_account_id = accounts[0]['account_id']

    for v in VendorCredit.objects.all():
        if v.zoho_id:
            skipped += 1
            continue

        vendor_id = _resolve_vendor_id(v.vendor_name, config)
        if not vendor_id:
            failed += 1
            print(f"[VendorCredit] No vendor found for: {v.vendor_name}")
            continue

        payload = {
            'vendor_id':            vendor_id,
            'vendor_credit_number': str(v.vendor_credit_number) if v.vendor_credit_number else '',
            'date':                 str(v.vendor_credit_date) if v.vendor_credit_date else '',
            'line_items': [{
                'account_id':  fallback_account_id,
                'description': f'Vendor Credit {v.vendor_credit_number}',
                'rate':        float(v.amount or 0),
                'quantity':    1
            }],
        }
        resp = _zoho_post(f"{ZOHO_BOOKS_BASE}/vendorcredits?organization_id={org}", payload, config)
        if resp.status_code in (200, 201):
            v.mark_migrated(resp.json().get('vendor_credit', {}).get('vendor_credit_id', ''))
            success += 1
        else:
            failed += 1
            print(f"[VendorCredit] Failed: {v.vendor_credit_number} → {resp.text}")

    results['vendor_credits'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ VENDOR CREDITS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_journals(config, results):
    """
    Use actual Tally account names (stored in narration as JSON)
    to correctly map debit/credit legs in Zoho instead of using a fake
    fallback expense account for both sides.
    """
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    account_map = _build_zoho_account_map(config)

    expense_account_map = {}
    for acct_type in ['expense', 'other_expense', 'cost_of_goods_sold', 'other_current_liability']:
        r = _zoho_get(
            f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type={acct_type}",
            config
        )
        if r.status_code == 200:
            for a in r.json().get('chartofaccounts', []):
                expense_account_map[a['account_name'].strip().lower()] = a['account_id']

    acct_resp = _zoho_get(f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type=expense", config)
    fallback_account_id = ''
    if acct_resp.status_code == 200:
        accts = acct_resp.json().get('chartofaccounts', [])
        if accts:
            fallback_account_id = accts[0]['account_id']

    for j in Journal.objects.all():
        if j.zoho_id:
            skipped += 1
            continue

        journal_lines = []
        narration_text = j.narration or ''
        if '__lines__' in narration_text:
            parts = narration_text.split('__lines__', 1)
            narration_text = parts[0]
            try:
                stored_lines = json.loads(parts[1])
                for line in stored_lines:
                    acct_name = line.get('account_name', '').strip()
                    acct_id = account_map.get(acct_name.lower(), fallback_account_id)
                    debit  = float(line.get('debit',  0) or 0)
                    credit = float(line.get('credit', 0) or 0)
                    if debit > 0:
                        journal_lines.append({
                            'account_id':      acct_id,
                            'description':     acct_name,
                            'debit_or_credit': 'debit',
                            'amount':          debit,
                        })
                    elif credit > 0:
                        journal_lines.append({
                            'account_id':      acct_id,
                            'description':     acct_name,
                            'debit_or_credit': 'credit',
                            'amount':          credit,
                        })
            except (json.JSONDecodeError, Exception) as e:
                print(f"[Journal] Could not parse lines for {j.voucher_number}: {e}")

        if not journal_lines:
            amt = float(j.amount or 0)
            journal_lines = [
                {'account_id': fallback_account_id, 'description': f'Journal {j.voucher_number}', 'debit_or_credit': 'debit',  'amount': amt},
                {'account_id': fallback_account_id, 'description': f'Journal {j.voucher_number}', 'debit_or_credit': 'credit', 'amount': amt},
            ]

        payload = {
            'journal_date': str(j.voucher_date) if j.voucher_date else '',
            'notes':        narration_text,
            'line_items':   journal_lines,
        }

        resp = _zoho_post(f"{ZOHO_BOOKS_BASE}/journals?organization_id={org}", payload, config)
        if resp.status_code in (200, 201):
            j.mark_migrated(resp.json().get('journal', {}).get('journal_id', ''))
            success += 1
        else:
            failed += 1
            print(f"[Journal] Failed: {j.voucher_number} → {resp.text}")

    results['journals'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ JOURNALS pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_opening_balances(config, results):
    """
    Use the correct Zoho API endpoint for opening balances:
    PUT /settings/openingbalances with an accounts array.
    """
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    unpushed = OpeningBalance.objects.filter(is_pushed=False)
    if not unpushed.exists():
        results['opening_balances'] = {'success': 0, 'failed': 0, 'skipped': OpeningBalance.objects.count()}
        return

    acct_resp = _zoho_get(f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}", config)
    if acct_resp.status_code != 200:
        results['opening_balances'] = {'success': 0, 'failed': unpushed.count(), 'skipped': 0}
        print(f"[OB] Could not fetch Zoho chart of accounts: {acct_resp.text}")
        return

    zoho_accounts = {
        a['account_name'].strip().lower(): a['account_id']
        for a in acct_resp.json().get('chartofaccounts', [])
    }

    accounts_payload = []
    ob_records = []

    for ob in unpushed:
        zoho_account_id = zoho_accounts.get(ob.ledger_name.strip().lower())
        if not zoho_account_id:
            skipped += 1
            print(f"[OB] No Zoho account matched for: {ob.ledger_name}")
            continue

        accounts_payload.append({
            'account_id':      zoho_account_id,
            'debit_or_credit': ob.balance_type,
            'amount':          ob.opening_balance,
        })
        ob_records.append((ob, zoho_account_id))

    if not accounts_payload:
        results['opening_balances'] = {'success': 0, 'failed': 0, 'skipped': skipped}
        return

    url = f"{ZOHO_BOOKS_BASE}/settings/openingbalances?organization_id={org}"
    payload = {'accounts': accounts_payload}
    resp = _zoho_put(url, payload, config)

    if resp.status_code in (200, 201):
        for ob, zoho_account_id in ob_records:
            ob.zoho_account_id = zoho_account_id
            ob.is_pushed = True
            ob.save(update_fields=['zoho_account_id', 'is_pushed', 'synced_at'])
        success = len(ob_records)
        print(f"[OB] Successfully pushed {success} opening balances")
    else:
        failed = len(ob_records)
        print(f"[OB] Failed to push opening balances: {resp.text}")

    results['opening_balances'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"✅ OPENING BALANCES pushed → success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


def _push_expenses(config, results, account_map=None):
    org = config.organization_id
    success, failed, skipped = 0, 0, 0

    if account_map is None:
        account_map = _build_zoho_account_map(config)

    expense_account_map = {}
    default_expense_id = None
    for acct_type in ['expense', 'other_expense', 'cost_of_goods_sold']:
        r = _zoho_get(
            f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type={acct_type}",
            config
        )
        if r.status_code == 200:
            for a in r.json().get('chartofaccounts', []):
                expense_account_map[a['account_name'].strip().lower()] = a['account_id']
                if default_expense_id is None:
                    default_expense_id = a['account_id']
                    print(f"[Expense] Default expense account: {a['account_name']} -> {default_expense_id}")

    paid_through_map = {}
    default_paid_through_id = None
    for acct_type in ['cash', 'bank']:
        r = _zoho_get(
            f"{ZOHO_BOOKS_BASE}/chartofaccounts?organization_id={org}&account_type={acct_type}",
            config
        )
        if r.status_code == 200:
            for a in r.json().get('chartofaccounts', []):
                paid_through_map[a['account_name'].strip().lower()] = a['account_id']
                if default_paid_through_id is None:
                    default_paid_through_id = a['account_id']
                    print(f"[Expense] Default paid_through: {a['account_name']} -> {default_paid_through_id}")

    for exp in Expense.objects.all():
        if exp.zoho_id:
            skipped += 1
            continue

        account_id = expense_account_map.get(exp.account_name.strip().lower(), default_expense_id)
        if not account_id:
            failed += 1
            print(f"[Expense] No expense account found for: {exp.account_name}")
            continue

        paid_through_id = paid_through_map.get(
            exp.paid_through.strip().lower() if exp.paid_through else '',
            default_paid_through_id
        )

        print(f"[Expense] {exp.payment_number} | account: {exp.account_name} -> {account_id} | paid_through: {exp.paid_through} -> {paid_through_id}")

        payload = {
            'account_id':       account_id,
            'date':             str(exp.payment_date) if exp.payment_date else '',
            'amount':           float(exp.amount or 0),
            'description':      exp.narration or exp.account_name,
            'reference_number': str(exp.payment_number),
            'is_billable':      False,
        }
        if paid_through_id:
            payload['paid_through_account_id'] = paid_through_id

        url = f"{ZOHO_BOOKS_BASE}/expenses?organization_id={org}"
        resp = _zoho_post(url, payload, config)

        if resp.status_code in (200, 201):
            exp.mark_migrated(resp.json().get('expense', {}).get('expense_id', ''))
            success += 1
            print(f"[Expense] Pushed: {exp.payment_number}")
        else:
            failed += 1
            print(f"[Expense] Failed: {exp.payment_number} -> {resp.json().get('message', resp.text[:100])}")

    results['expenses'] = {'success': success, 'failed': failed, 'skipped': skipped}
    print(f"{'='*50}")
    print(f"EXPENSES pushed -> success: {success} | failed: {failed} | skipped: {skipped}")
    print(f"{'='*50}")


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

        push_types = body.get('types', [
            'customers', 'vendors', 'accounts', 'items', 'taxes',
            'invoices', 'receipts', 'bills', 'payments',
            'credit_notes', 'vendor_credits', 'journals', 'opening_balances',
            'expenses'
        ])

        def run_push():
            results = {}
            errors = []
            for push_type, push_fn in [
                ('customers',        _push_customers),
                ('vendors',          _push_vendors),
                ('accounts',         _push_accounts),
                ('items',            _push_items),
                ('taxes',            _push_taxes),
                ('invoices',         _push_invoices),
                ('receipts',         _push_receipts),
                ('bills',            _push_bills),
                ('payments',         _push_payments),
                ('credit_notes',     _push_credit_notes),
                ('vendor_credits',   _push_vendor_credits),
                ('journals',         _push_journals),
                ('opening_balances', _push_opening_balances),
                ('expenses',         _push_expenses),
            ]:
                if push_type in push_types:
                    try:
                        push_fn(config, results)
                    except Exception as e:
                        errors.append(f"{push_type}: {str(e)}")
                        print(f"[Push] Error in {push_type}: {e}")

            total_success = sum(v.get('success', 0) for v in results.values())
            total_failed  = sum(v.get('failed',  0) for v in results.values())
            total_skipped = sum(v.get('skipped', 0) for v in results.values())
            print(f"[Push] DONE → success: {total_success} | failed: {total_failed} | skipped: {total_skipped}")

        thread = threading.Thread(target=run_push, daemon=True)
        thread.start()

        return JsonResponse({
            'message': 'Push started in background. Check server logs for progress.',
            'status':  'running'
        }, status=202)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- MISC ----------------

@csrf_exempt
def migration_status_all(request):
    """
    Returns detailed migration status for every model.
    Used by the dashboard to show accurate pushed/pending counts.
    """
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        def counts(model, use_is_pushed=False):
            total = model.objects.count()
            if use_is_pushed:
                migrated = model.objects.filter(is_pushed=True).count()
            else:
                migrated = model.objects.filter(
                    zoho_id__isnull=False
                ).exclude(zoho_id='').exclude(zoho_id='None').count()
            return {'total': total, 'migrated': migrated, 'pending': total - migrated}

        data = {
            'masters': {
                'customers': counts(Customer),
                'vendors':   counts(Vendor),
                'accounts':  counts(Account),
                'items':     counts(Item),
                'taxes':     counts(Tax),
            },
            'transactions': {
                'invoices':         counts(Invoice),
                'receipts':         counts(Receipt),
                'bills':            counts(Purchase),
                'payments':         counts(Payment),
                'credit_notes':     counts(CreditNote),
                'vendor_credits':   counts(VendorCredit),
                'journals':         counts(Journal),
                'expenses':         counts(Expense),
                'opening_balances': counts(OpeningBalance, use_is_pushed=True),
            },
        }

        all_models = list(data['masters'].values()) + list(data['transactions'].values())
        data['summary'] = {
            'total':    sum(m['total']    for m in all_models),
            'migrated': sum(m['migrated'] for m in all_models),
            'pending':  sum(m['pending']  for m in all_models),
        }

        return JsonResponse(data, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_next_task(request):
    return JsonResponse({'task': 'fetch_customers'})


@csrf_exempt
def receive_tax(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        taxes = data.get('taxes', [])

        for t in taxes:
            Tax.objects.update_or_create(
                tax_name=t.get('tax_name', ''),
                defaults={
                    'tax_rate':    t.get('tax_rate', 0),
                    'tax_type':    t.get('tax_type', ''),
                    'ledger_name': t.get('ledger_name', ''),
                    'parent':      None,
                    'is_active':   t.get('is_active', True),
                }
            )

        print(f"Received {len(taxes)} tax records")
        return JsonResponse({'status': 'received', 'count': len(taxes)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_opening_balances(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        balances = data.get('balances', [])

        for b in balances:
            OpeningBalance.objects.update_or_create(
                ledger_name=b.get('ledger_name', ''),
                defaults={
                    'parent':          b.get('parent', ''),
                    'opening_balance': b.get('opening_balance', 0),
                    'balance_type':    b.get('balance_type', 'debit'),
                    'is_pushed':       False,
                }
            )
        print(f"Saved {len(balances)} opening balances")
        return JsonResponse({'status': 'received', 'count': len(balances)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- DASHBOARD FUNCTIONS ----------------

@csrf_exempt
def customer_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Customer.objects.count()
        migrated = Customer.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_ledgers': list(Customer.objects.values(
                'name', 'email', 'phone', 'state', 'pincode', 'country', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def vendor_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Vendor.objects.count()
        migrated = Vendor.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_ledgers': list(Vendor.objects.values(
                'name', 'email', 'phone', 'state', 'pincode', 'country', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def coa_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Account.objects.count()
        migrated = Account.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_ledgers': list(Account.objects.values(
                'account_name', 'account_code', 'account_type', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def items_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Item.objects.count()
        migrated = Item.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_items': list(Item.objects.values(
                'name', 'rate', 'description', 'sku',
                'product_type', 'gst_rate', 'hsn_code', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def invoice_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Invoice.objects.count()
        migrated = Invoice.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_invoices': list(Invoice.objects.values(
                'invoice_number', 'customer_name', 'invoice_date', 'total_amount', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receipt_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Receipt.objects.count()
        migrated = Receipt.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_receipts': list(Receipt.objects.values(
                'receipt_number', 'customer_name', 'receipt_date',
                'amount', 'payment_mode', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def credit_note_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = CreditNote.objects.count()
        migrated = CreditNote.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_credit_notes': list(CreditNote.objects.values(
                'credit_note_number', 'customer_name', 'credit_note_date', 'amount', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def bill_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Purchase.objects.count()
        migrated = Purchase.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_bills': list(Purchase.objects.values(
                'bill_number', 'vendor_name', 'bill_date', 'amount', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def payment_made_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Payment.objects.count()
        migrated = Payment.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_payments': list(Payment.objects.values(
                'payment_number', 'vendor_name', 'payment_date',
                'amount', 'payment_mode', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def vendor_credit_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = VendorCredit.objects.count()
        migrated = VendorCredit.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_vendor_credits': list(VendorCredit.objects.values(
                'vendor_credit_number', 'vendor_name', 'vendor_credit_date', 'amount', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def expense_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Expense.objects.count()
        migrated = Expense.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_expenses': list(Expense.objects.values(
                'payment_number', 'payment_date', 'account_name',
                'paid_through', 'amount', 'narration', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def journal_dashboard(request):
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        total = Journal.objects.count()
        migrated = Journal.objects.filter(zoho_id__isnull=False).exclude(zoho_id='').count()
        return JsonResponse({
            'summary': {
                'fetched_from_tally':      total,
                'pushed_to_zoho':          migrated,
                'pending_to_push_to_zoho': total - migrated
            },
            'all_journals': list(Journal.objects.values(
                'voucher_number', 'voucher_date', 'narration', 'amount', 'zoho_id'
            ).annotate(pushed_to_zoho=models.Case(
                models.When(zoho_id__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField()
            ))
        )})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- SETTINGS FUNCTIONS ----------------

@csrf_exempt
def get_zoho_connection_status(request):
    if request.method == 'GET':
        try:
            payload = verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        user_email = payload.get('email')
        try:
            config = ZohoConfig.objects.get(user_email=user_email)
            resp = req.get(
                f"{ZOHO_BOOKS_BASE}/organizations",
                headers={'Authorization': f'Zoho-oauthtoken {config.access_token}'}
            )
            if resp.status_code == 401:
                _refresh_zoho_token(config)
                status = 'connected'
            else:
                status = 'connected' if resp.status_code == 200 else 'error'
            return JsonResponse({
                'status':          status,
                'organization_id': config.organization_id,
                'client_id':       config.client_id,
            })
        except ZohoConfig.DoesNotExist:
            return JsonResponse({'status': 'not_connected'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def test_tally_connection(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        host = data.get('host', 'localhost')
        port = data.get('port', 9000)
        try:
            req.post(
                f"http://{host}:{port}",
                data="<ENVELOPE><HEADER><TALLYREQUEST>Export</TALLYREQUEST></HEADER></ENVELOPE>",
                timeout=5
            )
            return JsonResponse({'status': 'connected', 'message': 'Tally is reachable'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        try:
            payload = verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if not current_password or not new_password:
            return JsonResponse({'error': 'Both passwords required'}, status=400)
        user = AppUser.objects.get(email=payload.get('email'))
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
            return JsonResponse({'error': 'Current password is incorrect'}, status=400)
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed.decode('utf-8')
        user.save()
        return JsonResponse({'message': 'Password changed successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def clear_migration_data(request):
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        Invoice.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Receipt.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Purchase.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Payment.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        CreditNote.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        VendorCredit.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Journal.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Expense.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Account.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        Item.objects.all().update(zoho_id=None, zoho_migrated_at=None)
        OpeningBalance.objects.all().update(is_pushed=False, zoho_account_id=None)
        Customer.objects.all().update(zoho_id=None)
        Vendor.objects.all().update(zoho_id=None)
        return JsonResponse({'message': 'All migration data cleared. You can re-sync now.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def approve_invoices_in_zoho(request):
    """Submit (approve) all pushed invoices in Zoho Books."""
    if request.method == 'POST':
        try:
            payload = verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        try:
            config = _get_zoho_config(payload.get('email'))
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        org = config.organization_id
        success, failed, skipped = 0, 0, 0

        for inv in Invoice.objects.exclude(zoho_id__isnull=True).exclude(zoho_id=''):
            url = f"{ZOHO_BOOKS_BASE}/invoices/{inv.zoho_id}/submit?organization_id={org}"
            resp = _zoho_post(url, {}, config)
            if resp.status_code in (200, 201):
                success += 1
            else:
                failed += 1
                print(f"[Approve] Failed: {inv.invoice_number} → {resp.text}")

        return JsonResponse({
            'success': success,
            'failed':  failed,
            'skipped': skipped,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def exchange_zoho_code(request):
    """
    Called by Setup.jsx after Zoho redirects back with ?code=...
    Receives { client_id, client_secret, code, redirect_uri }
    Exchanges the one-time code for access_token + refresh_token via Zoho India.
    Returns { access_token, refresh_token } to the frontend.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    client_id     = (body.get('client_id')     or '').strip()
    client_secret = (body.get('client_secret') or '').strip()
    code          = (body.get('code')          or '').strip()
    redirect_uri  = (body.get('redirect_uri')  or '').strip()

    if not all([client_id, client_secret, code, redirect_uri]):
        return JsonResponse(
            {'error': 'client_id, client_secret, code, and redirect_uri are all required.'},
            status=400,
        )

    try:
        response = req.post(
            'https://accounts.zoho.in/oauth/v2/token',
            params={
                'grant_type':    'authorization_code',
                'client_id':     client_id,
                'client_secret': client_secret,
                'redirect_uri':  redirect_uri,
                'code':          code,
            },
            timeout=15,
        )
        data = response.json()
    except req.exceptions.Timeout:
        return JsonResponse({'error': 'Request to Zoho timed out. Please try again.'}, status=504)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if 'error' in data:
        return JsonResponse(
            {'error': f"Zoho returned an error: {data['error']}. The code may have expired — please try again."},
            status=400,
        )

    access_token  = data.get('access_token', '')
    refresh_token = data.get('refresh_token', '')

    if not access_token or not refresh_token:
        return JsonResponse(
            {'error': 'Zoho did not return tokens. Check your Client ID, Secret, and redirect URI.'},
            status=400,
        )

    return JsonResponse({
        'access_token':  access_token,
        'refresh_token': refresh_token,
    }, status=200)

