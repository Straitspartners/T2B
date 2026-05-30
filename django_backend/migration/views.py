from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AppUser
import json
import jwt
import datetime
import bcrypt
import os

# ✅ FIX 3: Load SECRET_KEY from environment variable (never hardcode in production)
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key_here_minimum_32_characters_long")


# ---------------- AUTH HELPERS ----------------

def verify_token(request):
    """Returns decoded payload or raises exception."""
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
    """
    ✅ FIX 2: The agent sends 'username' field (e.g. 'cloud'), but the DB stores email.
    This helper tries email lookup first, then falls back to username lookup.
    """
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

        user = AppUser.objects.create(
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

        # ✅ FIX 2: support login by email or username
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
    """
    ✅ Token endpoint for the desktop sync agent (python_agent.py).
    Called via config.json → auth_url → /api/generate_token_agent/
    Accepts username (or email) + password, returns a Bearer token.
    Supports both JSON and form-data payloads.
    """
    if request.method == 'POST':
        try:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' in content_type:
                data = json.loads(request.body)
                identifier = data.get('username') or data.get('email')
                password = data.get('password')
            else:
                # form-data (default from desktop agent)
                identifier = request.POST.get('username') or request.POST.get('email')
                password = request.POST.get('password')
        except (json.JSONDecodeError, Exception) as e:
            return JsonResponse({'error': f'Bad request body: {str(e)}'}, status=400)

        if not identifier or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        # ✅ FIX 2: look up by email first, then username
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
        test_response = req.get(
            'https://www.zohoapis.com/books/v3/organizations',
            headers=headers
        )

        print("Zoho status:", test_response.status_code)
        print("Zoho response:", test_response.json())

        if test_response.status_code != 200:
            return JsonResponse({
                'error': 'Invalid Zoho credentials. Please check and try again.',
                'zoho_response': test_response.json()
            }, status=400)

        return JsonResponse({'message': 'Zoho Books connected successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ---------------- AGENT DATA RECEIVERS ----------------

@csrf_exempt
def receive_customers(request):
    """Receives customer ledgers from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])
        print(f"Received {len(ledgers)} customers")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(ledgers)}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_vendors(request):
    """Receives vendor ledgers from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        ledgers = data.get('ledgers', [])
        print(f"Received {len(ledgers)} vendors")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(ledgers)}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_accounts(request):
    """Receives Chart of Accounts from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        accounts = data.get('accounts', [])
        print(f"Received {len(accounts)} accounts")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(accounts)}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_items(request):
    """Receives stock items from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        items = data.get('items', [])
        print(f"Received {len(items)} items")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(items)}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_invoices(request):
    """Receives sales invoices from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        invoices = data.get('invoices', [])
        print(f"Received {len(invoices)} invoices")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(invoices)}, status=201)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def receive_receipts(request):
    """Receives payment receipts from the sync agent."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        data = json.loads(request.body)
        receipts = data.get('receipts', [])
        print(f"Received {len(receipts)} receipts")
        # TODO: save to DB / forward to Zoho Books
        return JsonResponse({'status': 'received', 'count': len(receipts)}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def data_migration_status(request):
    """Returns dashboard migration status counts."""
    if request.method == 'GET':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        # TODO: Replace with real DB counts later
        return JsonResponse({
            'fetched_from_tally': 0,
            'migrated_to_zoho': 0,
            'pending_migration_to_zoho': 0,
            'customers': 0,
            'vendors': 0,
            'COA': 0,
            'items': 0,
            'invoices': 0,
            'receipts': 0,
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

        # TODO: Replace with real DB counts later
        return JsonResponse({
            'total': 0,
            'migrated': 0,
            'pending': 0,
            'total_trans': 0,
            'transactions_migrated': 0,
            'transactions_pending': 0,
        }, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def push_to_zoho(request):
    """Pushes data to Zoho Books."""
    if request.method == 'POST':
        try:
            verify_token(request)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        return JsonResponse({'message': 'Sync started successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def get_next_task(request):
    """Polling endpoint for the sync agent."""
    return JsonResponse({'task': 'fetch_customers'})