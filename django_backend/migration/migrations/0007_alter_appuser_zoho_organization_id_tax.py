# migration/migrations/0007_alter_appuser_zoho_organization_id_tax.py

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('migration', '0006_appuser_zoho_refresh_token_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appuser',
            old_name='zoho_organization_id',
            new_name='zoho_org_id',
        ),
        migrations.AlterField(
            model_name='appuser',
            name='zoho_org_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tax_name', models.CharField(max_length=150)),
                ('tax_rate', models.FloatField()),
                ('tax_type', models.CharField(blank=True, max_length=50, null=True)),
                ('ledger_name', models.CharField(blank=True, max_length=150, null=True)),
                ('parent', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('synced_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]