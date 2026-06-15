from django.db import models


# ── HELPER MIXIN ─────────────────────────────────────────────────────────────
# Every migrated model inherits this so tracking is always consistent.

class ZohoMigrationMixin(models.Model):
    """
    Adds zoho_id, zoho_migrated_at to any model.
    is_migrated property returns True if zoho_id is set.
    """
    zoho_id          = models.CharField(max_length=100, blank=True, null=True)
    zoho_migrated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_migrated(self):
        return bool(self.zoho_id)

    def mark_migrated(self, zoho_id):
        """Call this after a successful Zoho push to stamp the record."""
        from django.utils import timezone
        self.zoho_id = zoho_id
        self.zoho_migrated_at = timezone.now()
        self.save(update_fields=['zoho_id', 'zoho_migrated_at'])

    def reset_migration(self):
        """Call this to force a re-push on next run."""
        self.zoho_id = None
        self.zoho_migrated_at = None
        self.save(update_fields=['zoho_id', 'zoho_migrated_at'])


# ── USER ──────────────────────────────────────────────────────────────────────

class AppUser(models.Model):
    username   = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # Legacy fields — kept for backwards compat, ZohoConfig is the real store
    zoho_access_token  = models.TextField(null=True, blank=True)
    zoho_client_id     = models.CharField(max_length=255, null=True, blank=True)
    zoho_client_secret = models.CharField(max_length=255, null=True, blank=True)
    zoho_org_id        = models.CharField(max_length=100, null=True, blank=True)
    zoho_refresh_token = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.email


# ── ZOHO CREDENTIALS ─────────────────────────────────────────────────────────

class ZohoCredentials(models.Model):
    """Legacy model — ZohoConfig is the active one."""
    user            = models.OneToOneField(AppUser, on_delete=models.CASCADE, null=True, blank=True)
    client_id       = models.CharField(max_length=255)
    client_secret   = models.CharField(max_length=255)
    access_token    = models.TextField()
    refresh_token   = models.TextField()
    organization_id = models.CharField(max_length=100)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Zoho credentials for org {self.organization_id}"


class ZohoConfig(models.Model):
    """
    Active Zoho credentials store — one row per logged-in user.
    Stores OAuth tokens and org ID needed to call Zoho Books API.
    """
    user_email      = models.EmailField(unique=True)
    client_id       = models.CharField(max_length=255)
    client_secret   = models.CharField(max_length=255)
    access_token    = models.TextField()
    refresh_token   = models.TextField()
    organization_id = models.CharField(max_length=100)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ZohoConfig({self.user_email})"


# ── MASTERS ───────────────────────────────────────────────────────────────────

class Customer(ZohoMigrationMixin):
    name       = models.CharField(max_length=255, unique=True)
    email      = models.CharField(max_length=254, blank=True, null=True)
    phone      = models.CharField(max_length=50, blank=True, null=True)
    address    = models.CharField(max_length=500, blank=True, null=True)
    state      = models.CharField(max_length=100, blank=True, null=True)
    pincode    = models.CharField(max_length=20, blank=True, null=True)
    country    = models.CharField(max_length=100, blank=True, null=True, default='India')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'migration_customer'

    def __str__(self):
        return self.name


class Vendor(ZohoMigrationMixin):
    name       = models.CharField(max_length=255, unique=True)
    email      = models.CharField(max_length=254, blank=True, null=True)
    phone      = models.CharField(max_length=50, blank=True, null=True)
    address    = models.CharField(max_length=500, blank=True, null=True)
    state      = models.CharField(max_length=100, blank=True, null=True)
    pincode    = models.CharField(max_length=20, blank=True, null=True)
    country    = models.CharField(max_length=100, blank=True, null=True, default='India')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'migration_vendor'

    def __str__(self):
        return self.name


class Account(ZohoMigrationMixin):
    account_name = models.CharField(max_length=255, unique=True)
    account_code = models.CharField(max_length=255, blank=True, default='')
    account_type = models.CharField(max_length=100, blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_name


class Item(ZohoMigrationMixin):
    name           = models.CharField(max_length=255, unique=True)
    rate           = models.CharField(max_length=50, default='0')
    description    = models.TextField(blank=True, default='')
    sku            = models.CharField(max_length=255, blank=True, default='')
    product_type   = models.CharField(max_length=255, blank=True, default='')
    gst_applicable = models.CharField(max_length=100, blank=True, default='')
    gst_rate       = models.CharField(max_length=50, blank=True, default='0')
    hsn_code       = models.CharField(max_length=100, blank=True, default='')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    type_of_supply = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ('Goods', 'Goods'),
            ('Services', 'Services'),
            ('Goods & Services', 'Goods & Services'),
            ('Unknown', 'Unknown'),
        ],
        help_text='Type of Supply for GST'
    )
    
    def __str__(self):
        return self.name


class Tax(ZohoMigrationMixin):
    tax_name    = models.CharField(max_length=150)
    tax_rate    = models.FloatField()
    tax_type    = models.CharField(max_length=50, null=True, blank=True)
    ledger_name = models.CharField(max_length=150, null=True, blank=True)
    parent      = models.CharField(max_length=255, null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    synced_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'migration_tax'

    def __str__(self):
        return self.tax_name


# ── TRANSACTIONS ──────────────────────────────────────────────────────────────

class Invoice(ZohoMigrationMixin):
    customer_name  = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date   = models.DateField(null=True, blank=True)
    total_amount   = models.CharField(max_length=50, default='0')
    cgst           = models.CharField(max_length=50, default='0')
    sgst           = models.CharField(max_length=50, default='0')
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class InvoiceLineItem(models.Model):
    """
    Individual line items for an Invoice.
    Not pushed to Zoho separately — used when building the invoice payload.
    """
    invoice      = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    item_name    = models.CharField(max_length=255)
    # quantity_raw = models.CharField(max_length=100, default='1 Nos')
    qty_value    = models.DecimalField(max_digits=14, decimal_places=4, default=1)
    qty_unit     = models.CharField(max_length=50, default='Nos')
    amount       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    rate         = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.invoice.invoice_number} | {self.item_name}"


class Receipt(ZohoMigrationMixin):
    customer_name  = models.CharField(max_length=255)
    receipt_number = models.CharField(max_length=100, unique=True)
    receipt_date   = models.DateField(null=True, blank=True)
    amount         = models.CharField(max_length=50, default='0')
    payment_mode   = models.CharField(max_length=100, default='')
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number


class Purchase(ZohoMigrationMixin):
    """Bills received from vendors."""
    vendor_name  = models.CharField(max_length=255)
    bill_number  = models.CharField(max_length=100, unique=True)
    bill_date    = models.DateField(null=True, blank=True)
    amount       = models.CharField(max_length=50, default='0')
    cgst         = models.CharField(max_length=50, default='0')   # added
    sgst         = models.CharField(max_length=50, default='0')   # added
    igst         = models.CharField(max_length=50, default='0')   # added
    total_amount = models.CharField(max_length=50, default='0')   # added

    def __str__(self):
        return self.bill_number


class PurchaseLineItem(models.Model):
    """
    Individual line items for a Purchase/Bill.
    Not pushed to Zoho separately — used when building the bill payload.
    """
    purchase  = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='line_items')
    item_name = models.CharField(max_length=255)
    quantity  = models.CharField(max_length=100, default='1')
    amount    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    rate      = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.purchase.bill_number} | {self.item_name}"


class Payment(ZohoMigrationMixin):
    """Payments made to vendors."""
    vendor_name    = models.CharField(max_length=255)
    payment_number = models.CharField(max_length=100, unique=True)
    payment_date   = models.DateField(null=True, blank=True)
    amount         = models.CharField(max_length=50, default='0')
    payment_mode   = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.payment_number


class CreditNote(ZohoMigrationMixin):
    customer_name      = models.CharField(max_length=255)
    credit_note_number = models.CharField(max_length=100, unique=True)
    credit_note_date   = models.DateField(null=True, blank=True)
    amount             = models.CharField(max_length=50, default='0')
    cgst               = models.CharField(max_length=50, default='0')   # added
    sgst               = models.CharField(max_length=50, default='0')   # added
    igst               = models.CharField(max_length=50, default='0')   # added
    total_amount       = models.CharField(max_length=50, default='0')   # added

    def __str__(self):
        return self.credit_note_number


class VendorCredit(ZohoMigrationMixin):
    vendor_name          = models.CharField(max_length=255)
    vendor_credit_number = models.CharField(max_length=100, unique=True)
    vendor_credit_date   = models.DateField(null=True, blank=True)
    amount               = models.CharField(max_length=50, default='0')

    def __str__(self):
        return self.vendor_credit_number


class Journal(ZohoMigrationMixin):
    voucher_number = models.CharField(max_length=100, unique=True)
    voucher_date   = models.DateField(null=True, blank=True)
    narration      = models.TextField(blank=True)
    amount         = models.CharField(max_length=50, default='0')

    def __str__(self):
        return self.voucher_number


class JournalLine(models.Model):
    """
    Individual debit/credit legs of a Journal entry.
    Not pushed separately — used when building the journal payload.
    """
    journal      = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
    account_name = models.CharField(max_length=255)
    debit        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit       = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.journal.voucher_number} | {self.account_name}"


class OpeningBalance(models.Model):
    """
    Uses is_pushed instead of zoho_id since Zoho's opening balance
    API is a bulk PUT — no individual record ID is returned.
    """
    ledger_name     = models.CharField(max_length=255, unique=True)
    parent          = models.CharField(max_length=255, blank=True, null=True)
    opening_balance = models.FloatField(default=0.0)
    balance_type    = models.CharField(max_length=10, default='debit')  # 'debit' or 'credit'
    zoho_account_id = models.CharField(max_length=100, blank=True, null=True)
    is_pushed       = models.BooleanField(default=False)
    synced_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'migration_openingbalance'

    @property
    def is_migrated(self):
        return self.is_pushed

    def __str__(self):
        return self.ledger_name


class Expense(ZohoMigrationMixin):
    """
    Direct expense payments (e.g. cash paid for electricity).
    Detected from Payment vouchers where debit side is an expense account.
    """
    payment_number = models.CharField(max_length=100, unique=True)
    payment_date   = models.DateField(null=True, blank=True)
    account_name   = models.CharField(max_length=255)
    paid_through   = models.CharField(max_length=255, default='Cash')
    amount         = models.CharField(max_length=50, default='0')
    narration      = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'migration_expense'

    def __str__(self):
        return f"{self.payment_number} | {self.account_name}"