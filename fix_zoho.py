import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
django.setup()

from migration.models import AppUser, ZohoConfig

for user in AppUser.objects.exclude(zoho_client_id=None).exclude(zoho_organization_id=None):
    ZohoConfig.objects.update_or_create(
        user_email=user.email,
        defaults={
            'client_id': user.zoho_client_id or '',
            'client_secret': user.zoho_client_secret or '',
            'access_token': user.zoho_access_token or '',
            'refresh_token': '',
            'organization_id': user.zoho_organization_id or '',
        }
    )
    print(f"Migrated: {user.email}")

print("Done")