from django.db import models


class AppUser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Invoice(models.Model):
    customer_name = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField(null=True, blank=True)
    total_amount = models.CharField(max_length=50, default='0')
    cgst = models.CharField(max_length=50, default='0')
    sgst = models.CharField(max_length=50, default='0')
    created_at = models.DateTimeField(auto_now_add=True)
    zoho_id = models.CharField(max_length=100, blank=True, null=True)
    zoho_migrated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.invoice_number

    @property
    def is_migrated(self):
        return bool(self.zoho_id)


class InvoiceLineItem(models.Model):
    """
    Stores individual line items for an Invoice as received from the Tally agent.

    Raw data shape from agent:
        {
            "item_name": "Product A",
            "quantity": "2 Nos",   # e.g. "1 Nos", "5 Kg", "3 Box"
            "amount": "500.00"     # total for the line (qty × rate)
        }

    qty_value and qty_unit are parsed from the raw quantity string.
    rate is derived as amount / qty_value (stored for Zoho push).
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    item_name = models.CharField(max_length=255)

    # Raw string exactly as received, e.g. "2 Nos"
    quantity_raw = models.CharField(max_length=100, default='1 Nos')

    # Parsed quantity fields
    qty_value = models.DecimalField(max_digits=14, decimal_places=4, default=1)
    qty_unit = models.CharField(max_length=50, default='Nos')

    # Total amount for the line (qty × rate) — as received from Tally
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Derived: amount / qty_value — used when pushing to Zoho
    rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.invoice.invoice_number} | {self.item_name} | {self.quantity_raw} | {self.amount}"


class Receipt(models.Model):
    customer_name = models.CharField(max_length=255)
    receipt_number = models.CharField(max_length=100, unique=True)
    receipt_date = models.DateField(null=True, blank=True)
    amount = models.CharField(max_length=50, default='0')
    payment_mode = models.CharField(max_length=100, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    zoho_id = models.CharField(max_length=100, blank=True, null=True)
    zoho_migrated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.receipt_number

    @property
    def is_migrated(self):
        return bool(self.zoho_id)


class ZohoCredentials(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, null=True, blank=True)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    access_token = models.TextField()
    refresh_token = models.TextField()
    organization_id = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Zoho credentials for org {self.organization_id}"


class ZohoConfig(models.Model):
    user_email = models.EmailField(unique=True)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    access_token = models.TextField()
    refresh_token = models.TextField()
    organization_id = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ZohoConfig({self.user_email})"