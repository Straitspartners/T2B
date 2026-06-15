from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('migration', '0016_purchaselineitem'),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE migration_customer ADD COLUMN state varchar(100);
            ALTER TABLE migration_customer ADD COLUMN pincode varchar(20);
            ALTER TABLE migration_customer ADD COLUMN country varchar(100) DEFAULT 'India';
            ALTER TABLE migration_customer ADD COLUMN zoho_id varchar(100);
            ALTER TABLE migration_customer ADD COLUMN zoho_migrated_at datetime;

            ALTER TABLE migration_vendor ADD COLUMN state varchar(100);
            ALTER TABLE migration_vendor ADD COLUMN pincode varchar(20);
            ALTER TABLE migration_vendor ADD COLUMN country varchar(100) DEFAULT 'India';
            ALTER TABLE migration_vendor ADD COLUMN zoho_id varchar(100);
            ALTER TABLE migration_vendor ADD COLUMN zoho_migrated_at datetime;
            """
        ),
    ]