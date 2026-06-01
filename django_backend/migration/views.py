from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AppUser
import json
import jwt
import datetime
import bcrypt
import os

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key_here_minimum_32_characters_long")


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
            verify_token(request)
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

        import requests as req
        headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
        test_response = req.get('https://www.zohoapis.com/books/v3/organizations', headers=headers)

        if test_response.status_code != 200:
            return JsonResponse({
                'error': 'Invalid Zoho credentials. Please check and try again.',
                'zoho_response': test_response.json()
            }, status=400)

        return JsonResponse({'message': 'Zoho Books connected successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- AGENT DATA RECEIVERS ----------------

# In-memory store for synced data counts (replace with DB models later)
_sync_store = {
    'customers': [],
    'vendors': [],
    'accounts': [],
    'items': [],
    'invoices': [],
    'receipts': [],
}

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
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        data = json.loads(request.body)
        invoices = data.get('invoices', [])
        _sync_store['invoices'] = invoices
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
        _sync_store['receipts'] = receipts
        print(f"Received {len(receipts)} receipts")
        return JsonResponse({'status': 'received', 'count': len(receipts)}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- DASHBOARD & MIGRATION STATUS ----------------

@csrf_exempt
def data_migration_status(request):
    """Returns dashboard migration status counts."""
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        customers = len(_sync_store['customers'])
        vendors = len(_sync_store['vendors'])
        coa = len(_sync_store['accounts'])
        items = len(_sync_store['items'])
        invoices = len(_sync_store['invoices'])
        receipts = len(_sync_store['receipts'])
        total = customers + vendors + coa + items + invoices + receipts

        return JsonResponse({
            'fetched_from_tally': total,
            'migrated_to_zoho': 0,
            'pending_migration_to_zoho': total,
            'customers': customers,
            'vendors': vendors,
            'COA': coa,
            'items': items,
            'invoices': invoices,
            'receipts': receipts,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def total_records(request):
    """Returns total records count for Quick Migration page."""
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
        transactions = len(_sync_store['invoices']) + len(_sync_store['receipts'])

        return JsonResponse({
            'total': masters,
            'migrated': 0,
            'pending': masters,
            'total_trans': transactions,
            'transactions_migrated': 0,
            'transactions_pending': transactions,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_masters(request):
    """Returns masters data for Masters page."""
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
    """Returns transactions data for Transactions page."""
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        activities = []
        sno = 1

        for inv in _sync_store['invoices']:
            activities.append({
                'sNo': sno, 'type': 'Invoice',
                'name': inv.get('customer_name', 'Unknown'),
                'status': 'Fetched',
                'lastMigrated': inv.get('invoice_date', '-'),
                'amount': inv.get('total_amount', '0.00')
            })
            sno += 1

        for rec in _sync_store['receipts']:
            activities.append({
                'sNo': sno, 'type': 'Receipt',
                'name': rec.get('customer_name', 'Unknown'),
                'status': 'Fetched',
                'lastMigrated': rec.get('receipt_date', '-'),
                'amount': rec.get('amount', '0.00')
            })
            sno += 1

        return JsonResponse({
            'activities': activities,
            'counts': {
                'invoices': len(_sync_store['invoices']),
                'receipts': len(_sync_store['receipts']),
            }
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- PUSH TO ZOHO ----------------

@csrf_exempt
def push_to_zoho(request):
    """Send synced data from Django to Zoho Books."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        # TODO: Implement actual Zoho Books API calls here
        return JsonResponse({
            'message': 'Data synced to Zoho Books successfully!',
            'status': 'success'
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_next_task(request):
    return JsonResponse({'task': 'fetch_customers'})