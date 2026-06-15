from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('migration', '0023_item_type_of_supply'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='supply_type_raw',
        ),
    ]
