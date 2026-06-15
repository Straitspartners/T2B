from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('migration', '0022_creditnote_cgst_creditnote_igst_creditnote_sgst_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='type_of_supply',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Goods', 'Goods'),
                    ('Services', 'Services'),
                    ('Goods & Services', 'Goods & Services'),
                    ('Unknown', 'Unknown'),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='supply_type_raw',
            field=models.CharField(
                blank=True,
                help_text='Raw value as exported from Tally',
                max_length=100,
                null=True,
            ),
        ),
    ]
