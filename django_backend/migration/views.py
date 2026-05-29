from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AppUser
import json
import jwt
import datetime
import bcrypt

SECRET_KEY = "your_secret_key_here_minimum_32_characters_long"

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return JsonResponse({'error': 'All fields are required'}, status=400)

        # Check if user exists
        if AppUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = AppUser.objects.create(
            username=username,
            email=email,
            password=hashed.decode('utf-8')  
        )

        # Generate JWT token
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')

        return JsonResponse({
            'token': token,
            'name': username,
            'email': email
        }, status=200)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def signin_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'All fields are required'}, status=400)

        try:
            user = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        # Generate JWT token
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')

        return JsonResponse({
            'token': token,
            'email': email,
            'name': user.username
        }, status=200)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def connect_zoho(request):
    if request.method == 'POST':
        # Verify token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication token not found. Please login again.'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired. Please login again.'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token. Please login again.'}, status=401)

        data = json.loads(request.body)
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        organization_id = data.get('organization_id')

        if not all([client_id, client_secret, access_token, refresh_token, organization_id]):
            return JsonResponse({'error': 'All Zoho credentials are required'}, status=400)

        # Test Zoho API
        import requests
        headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}
        test_response = requests.get(
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


@csrf_exempt
def receive_customers(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print("Received Customers:", data)
        return JsonResponse({'status': 'received'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_next_task(request):
    # Dummy response for agent polling
    return JsonResponse({'task': 'fetch_customers'})