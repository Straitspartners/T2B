import tkinter as tk
from tkinter import messagebox
import requests
import xml.etree.ElementTree as ET
import json
import os
import logging
import re
import traceback
from datetime import datetime
from tkcalendar import DateEntry
import sys

BANK_CASH_LEDGER_SET = None
VENDOR_NAMES_CACHE = None

# ---------------- CONFIG ----------------

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
AUTH_TOKEN = None

DEFAULT_CONFIG = {
    "tally_url": "http://localhost:9000",
    "auth_url": "http://localhost:8000/api/agent-token/",
    "django_api_url": "http://localhost:8000/api/receive-customers/",
    "django_url_vendors": "http://localhost:8000/api/receive-vendors/",
    "django_url_accounts": "http://localhost:8000/api/receive-accounts/",
    "django_url_items": "http://localhost:8000/api/receive-items/",
    "django_url_invoices": "http://localhost:8000/api/receive-invoices/",
    "django_url_receipts": "http://localhost:8000/api/receive-receipts/",
    "django_url_taxes": "http://localhost:8000/api/receive-tax/",
    "django_url_bills": "http://localhost:8000/api/receive-purchases/",
    "django_url_payments": "http://localhost:8000/api/receive-payments/",
    "django_url_credit_notes": "http://localhost:8000/api/receive-credit-notes/",
    "django_url_vendor_credits": "http://localhost:8000/api/receive-vendor-credits/",
    "django_url_journals": "http://localhost:8000/api/receive-journals/",
    "django_url_opening_balances": "http://localhost:8000/api/receive-opening-balances/",
    "django_url_expenses": "http://localhost:8000/api/receive-expenses/",
}

# ---------------- LOGGING ----------------

log_file = os.path.join(BASE_DIR, 'sync_agent.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8',
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
logging.getLogger().addHandler(console_handler)

log = logging.getLogger(__name__)

# ---------------- CONFIG LOADER ----------------

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            loaded = json.load(file)
            for key, val in DEFAULT_CONFIG.items():
                if key not in loaded:
                    loaded[key] = val
            return loaded
    else:
        with open(CONFIG_PATH, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG

config = load_config()
TALLY_URL                       = config["tally_url"]
AUTH_URL                        = config["auth_url"]
DJANGO_API_URL_CUSTOMERS        = config.get("django_api_url")
DJANGO_API_URL_VENDORS          = config.get("django_url_vendors")
DJANGO_API_URL_ACCOUNTS         = config.get("django_url_accounts")
DJANGO_API_URL_ITEMS            = config.get("django_url_items")
DJANGO_API_URL_INVOICES         = config.get("django_url_invoices")
DJANGO_API_URL_RECEIPTS         = config.get("django_url_receipts")
DJANGO_API_URL_TAXES            = config.get("django_url_taxes")
DJANGO_API_URL_BILLS            = config.get("django_url_bills")
DJANGO_API_URL_PAYMENTS         = config.get("django_url_payments")
DJANGO_API_URL_CREDIT_NOTES     = config.get("django_url_credit_notes")
DJANGO_API_URL_VENDOR_CREDITS   = config.get("django_url_vendor_credits")
DJANGO_API_URL_JOURNALS         = config.get("django_url_journals")
DJANGO_API_URL_OPENING_BALANCES = config.get("django_url_opening_balances")
DJANGO_API_URL_EXPENSES         = config.get("django_url_expenses")

# ---------------- TOKEN HANDLER ----------------

def get_token(username, password):
    global AUTH_TOKEN
    try:
        log.info(f"[AUTH] Logging in as '{username}'...")
        response = requests.post(AUTH_URL, data={"username": username, "password": password}, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        AUTH_TOKEN = token_data.get("token")
        if AUTH_TOKEN:
            log.info("[AUTH] ✅ Login successful")
            return True
        log.error("[AUTH] ❌ No token in response")
        return False
    except requests.exceptions.RequestException as e:
        log.error(f"[AUTH] ❌ Login failed: {e}")
        return False

def auth_headers():
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

# ---------------- TALLY REQUEST XML ----------------

TALLY_REQUEST_XML_CUSTOMERS = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Customer Ledgers</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Customer Ledgers" ISMODIFY="No">
        <TYPE>Ledger</TYPE><FILTER>IsSundryDebtor</FILTER>
        <FETCH>NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE</FETCH>
      </COLLECTION>
      <SYSTEM TYPE="Formulae" NAME="IsSundryDebtor">$Parent = "Sundry Debtors"</SYSTEM>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

TALLY_REQUEST_XML_VENDORS = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Vendor Ledgers</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Vendor Ledgers" ISMODIFY="No">
        <TYPE>Ledger</TYPE><FILTER>IsSundryCreditor</FILTER>
        <FETCH>NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE</FETCH>
      </COLLECTION>
      <SYSTEM TYPE="Formulae" NAME="IsSundryCreditor">$Parent = "Sundry Creditors"</SYSTEM>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

TALLY_REQUEST_XML_COA = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>All Ledgers</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="All Ledgers" ISMODIFY="No"><TYPE>Ledger</TYPE><FETCH>NAME, PARENT</FETCH></COLLECTION>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

TALLY_REQUEST_XML_ITEMS = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Stock Items</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Stock Items" ISMODIFY="No">
        <TYPE>StockItem</TYPE>
        <FETCH>NAME, RATE, DESCRIPTION, PARTNUMBER, PARENT, GSTAPPLICABLE, GSTDETAILS.RATE, GSTDETAILS.HSN</FETCH>
      </COLLECTION>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

TALLY_REQUEST_XML_TAXES = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Tax Ledgers</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Tax Ledgers" ISMODIFY="No">
        <TYPE>Ledger</TYPE><FILTER>IsTaxLedger</FILTER>
        <FETCH>NAME, PARENT, BASICRATEOFTAX, RATEOFTAXATION, PERCENTAGEOFTAXATION</FETCH>
        <COMPUTE>TAXRATE : $BasicRateOfTax</COMPUTE>
      </COLLECTION>
      <SYSTEM TYPE="Formulae" NAME="IsTaxLedger">$Parent = "Duties &amp; Taxes"</SYSTEM>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

TALLY_REQUEST_XML_OPENING_BALANCES = """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Opening Balances</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Opening Balances" ISMODIFY="No">
        <TYPE>Ledger</TYPE><FETCH>NAME, PARENT, OPENINGBALANCE</FETCH>
      </COLLECTION>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""

# ---------------- DYNAMIC XML BUILDER ----------------

def get_daybook_xml(from_date, to_date):
    """
    Fetch all vouchers using TDL Collection export.
    BUG FIX #2: Added REFERENCE to FETCH list so the human-readable invoice
    number (e.g. GST/2024-25/228) is available. VOUCHERNUMBER alone returns
    a sequential internal counter ('1','2','3') in Collection export mode.
    BUG FIX #6: Caller uses timeout=120 for this large request.
    """
    return f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>All Vouchers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVFROMDATE>{from_date}</SVFROMDATE>
        <SVTODATE>{to_date}</SVTODATE>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="All Vouchers" ISMODIFY="No">
            <TYPE>Voucher</TYPE>
            <FILTERS>VchDateFilter</FILTERS>
            <FETCH>
              DATE,
              VOUCHERTYPENAME,
              VOUCHERNUMBER,
              REFERENCE,
              MASTERID,
              NUMBERINGSTYLE,
              PARTYLEDGERNAME,
              BASICBUYERNAME,
              NARRATION,
              ISCANCELLED,
              ALLLEDGERENTRIES.LIST.LEDGERNAME,
              ALLLEDGERENTRIES.LIST.AMOUNT,
              ALLLEDGERENTRIES.LIST.ISPARTYLEDGER,
              ALLLEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME,
              ALLLEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.BILLTYPE,
              ALLINVENTORYENTRIES.LIST.STOCKITEMNAME,
              ALLINVENTORYENTRIES.LIST.ACTUALQTY,
              ALLINVENTORYENTRIES.LIST.AMOUNT
            </FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="VchDateFilter">
            $$Date:$Date &gt;= $$Date:"{from_date}" AND
            $$Date:$Date &lt;= $$Date:"{to_date}"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""

# ---------------- ACCOUNT TYPE MAP ----------------

TALLY_TO_ZOHO_ACCOUNT_TYPE = {
    "Bank Accounts": "bank",
    "Bank OCC A/c": "bank",
    "Bank OD A/c": "bank",
    "Branch / Divisions": "other_liability",
    "Capital Account": "equity",
    "Cash-in-Hand": "cash",
    "Current Assets": "other_current_asset",
    "Current Liabilities": "other_current_liability",
    "Deposits (Asset)": "other_current_asset",
    "Direct Expenses": "expense",
    "Direct Incomes": "income",
    "Duties & Taxes": "other_current_liability",
    "Expenses (Direct)": "expense",
    "Expenses (Indirect)": "other_expense",
    "Fixed Assets": "fixed_asset",
    "Income (Direct)": "income",
    "Income (Indirect)": "other_income",
    "Indirect Expenses": "other_expense",
    "Indirect Incomes": "other_income",
    "Investments": "other_current_asset",
    "Loans & Advances (Asset)": "other_current_asset",
    "Loans (Liability)": "long_term_liability",
    "Misc. Expenses (ASSET)": "other_asset",
    "Provisions": "other_current_liability",
    "Purchase Accounts": "cost_of_goods_sold",
    "Reserves & Surplus": "equity",
    "Retained Earnings": "income",
    "Sales Accounts": "income",
    "Secured Loans": "other_liability",
    "Stock-in-Hand": "cost_of_goods_sold",
    "Sundry Creditors": "accounts_payable",
    "Sundry Debtors": "accounts_receivable",
    "Suspense A/c": "other_liability",
    "Unsecured Loans": "loans_and_borrowing",
}

# ---------------- XML HELPERS ----------------

def clean_xml(xml_string):
    xml_string = re.sub(r'&#\d+;', '', xml_string)
    xml_string = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_string)
    return xml_string

def clean_xml(xml_string):
    xml_string = re.sub(r'&#\d+;', '', xml_string)
    xml_string = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_string)
    return xml_string

# ──────────────── INSERT NEW FUNCTION HERE ────────────────
def build_ledger_parent_map(xml_coa_data):
    """..."""
    ledger_parent_map = {}
    try:
        xml_data = clean_xml(xml_coa_data)
        root = ET.fromstring(xml_data)
        for ledger in root.findall(".//LEDGER"):
            name = (ledger.findtext(".//NAME") or "").strip().lower()
            parent = (ledger.findtext("PARENT") or "").strip().lower()
            if name:
                ledger_parent_map[name] = parent
        log.info(f"[PARSE] Built ledger-parent map: {len(ledger_parent_map)} ledgers")
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ Could not build ledger-parent map: {e}")
    return ledger_parent_map
# ──────────────── END NEW FUNCTION ────────────────

def _resolve_voucher_number(voucher, prefix, date_fmt=""):
    """
    Universal voucher number resolver — works across ALL Tally numbering styles.

    Tally companies number their vouchers in different ways:
      1. Auto (formatted) : VOUCHERNUMBER = 'GST/2024-25/001'  → use as-is
      2. Auto Retain       : VOUCHERNUMBER = '1','2','3'         → prefix it
      3. Manual            : REFERENCE    = 'INV-2024-001'       → use REFERENCE
      4. Bill allocation   : BILLALLOCATIONS.LIST.NAME           → use bill name
      5. None of above     : build from prefix + MASTERID

    Priority order (first non-empty wins):
      REFERENCE  →  formatted VOUCHERNUMBER  →  BILL ALLOC NAME
      →  prefix+VOUCHERNUMBER  →  prefix+MASTERID

    Args:
        voucher  : XML VOUCHER element
        prefix   : entity prefix e.g. 'INV', 'BILL', 'REC', 'PAY', 'CN', 'JV', 'EXP'
        date_fmt : formatted date string e.g. '2024-04-01' (used in fallback)

    Returns:
        str — a non-empty, Zoho-safe voucher number
    """
    vch_no    = (voucher.findtext("VOUCHERNUMBER") or "").strip()
    reference = (voucher.findtext("REFERENCE")     or "").strip()
    master_id = (voucher.findtext("MASTERID")      or "").strip()
    num_style = (voucher.findtext("NUMBERINGSTYLE") or "").strip().lower()

    # 1. REFERENCE field — manually entered by user, always the best source
    if reference:
        return reference

    # 2. VOUCHERNUMBER — use directly if it looks formatted (contains non-digit chars)
    #    e.g. 'GST/2024-25/001', 'INV-001', 'TI/24-25/100'
    if vch_no and not vch_no.isdigit():
        return vch_no

    # 3. Bill allocation name — sometimes stores the invoice reference
    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
        for ba in le.findall(".//BILLALLOCATIONS.LIST"):
            name = (ba.findtext("NAME") or "").strip()
            if name and name != vch_no:
                return name

    # 4. VOUCHERNUMBER is a plain integer — prefix it to make it Zoho-safe
    #    e.g. '1' → 'INV-1',  '344' → 'BILL-344'
    if vch_no and vch_no.isdigit():
        return f"{prefix}-{vch_no}"

    # 5. Last resort — use MASTERID with prefix
    if master_id:
        return f"{prefix}-M{master_id}"

    # 6. Absolute fallback — prefix + date (should never reach here)
    return f"{prefix}-{date_fmt.replace('-', '')}"


def _format_date(date_raw):
    date_raw = (date_raw or "").strip()
    try:
        if len(date_raw) == 8 and date_raw.isdigit():
            return f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}"
    except Exception:
        pass
    return date_raw

def _is_cash_bank_ledger(name):
    """
    Reliable check using Tally's own PARENT classification (Bank Accounts,
    Bank OCC A/c, Bank OD A/c, Cash-in-Hand) — not name guessing.
    Works for ANY client, regardless of what they named their bank/cash ledgers.
    """
    if not BANK_CASH_LEDGER_SET:
        return False
    return (name or "").strip() in BANK_CASH_LEDGER_SET


def _get_voucher_amount(voucher):
    """
    Extract the REAL counterparty (customer/vendor) and amount from a voucher.
    Tally sometimes marks the bank/cash ledger as ISPARTYLEDGER="Yes" by mistake
    (a data-entry quirk), which would otherwise make party_name = the bank name.
    This function actively excludes bank/cash ledgers (identified via Tally's
    own PARENT classification, not name keywords) when picking the party.
    Returns: (party_name, amount, is_pure_bank_transfer)
    """
    ledger_entries = []
    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
        ln = (le.findtext("LEDGERNAME") or "").strip()
        is_party = (le.findtext("ISPARTYLEDGER") or "").strip().lower() == "yes"
        try:
            amt = abs(float(le.findtext("AMOUNT") or "0.0"))
        except ValueError:
            amt = 0.0
        ledger_entries.append({"name": ln, "is_party": is_party, "amount": amt})

    # Priority 1 — ISPARTYLEDGER=Yes AND not a bank/cash account (the real party)
    for le in ledger_entries:
        if le["is_party"] and le["amount"] > 0 and not _is_cash_bank_ledger(le["name"]):
            return le["name"], le["amount"], False

    # Priority 2 — any non-bank/cash ledger with a nonzero amount
    for le in ledger_entries:
        if le["amount"] > 0 and not _is_cash_bank_ledger(le["name"]):
            return le["name"], le["amount"], False

    # Priority 3 — every ledger really IS bank/cash → genuine bank transfer
    fallback_name = voucher.findtext("PARTYLEDGERNAME") or voucher.findtext("BASICBUYERNAME") or "Unknown"
    total_amount = max((le["amount"] for le in ledger_entries), default=0.0)
    return fallback_name, total_amount, True

# ---------------- VOUCHER TYPE CLASSIFICATION ----------------

VOUCHER_TYPE_MAP = {
    # Sales
    "sales": "sales",
    "gst sales": "sales",
    "sales invoice": "sales",
    "tax invoice": "sales",
    "gst tax invoice": "sales",
    "sales - tax invoice": "sales",
    "retail invoice": "sales",
    "export invoice": "sales",
    "sales order": "sales",
    "pos invoice": "sales",
    # Purchase
    "purchase": "purchase",
    "gst purchase": "purchase",
    "purchase invoice": "purchase",
    "tax purchase invoice": "purchase",
    "purchase - tax invoice": "purchase",
    "import invoice": "purchase",
    "purchase order": "purchase",
    # Receipt
    "receipt": "receipt",
    "receipt voucher": "receipt",
    # Payment
    "payment": "payment",
    "payment voucher": "payment",
    # Credit Note
    "credit note": "credit_note",
    "credit note voucher": "credit_note",
    "sales return": "credit_note",
    # Debit Note
    "debit note": "debit_note",
    "debit note voucher": "debit_note",
    "purchase return": "debit_note",
    # Journal
    "journal": "journal",
    "journal voucher": "journal",
    # Contra (bank/cash transfers — skip)
    "contra": "contra",
}

def classify_voucher(vch_type_raw):
    """Return canonical type or None if unrecognised."""
    return VOUCHER_TYPE_MAP.get(vch_type_raw.strip().lower())

# ──────────────── INSERT NEW MAP + FUNCTION HERE ────────────────
GROUP_TO_TRANSACTION_KIND = {
    "bank accounts":          "transfer",
    "bank occ a/c":           "transfer",
    "bank od a/c":            "transfer",
    "cash-in-hand":           "contra",
    "capital account":        "journal_candidate",
    "reserves & surplus":     "journal_candidate",
    "loans (liability)":      "journal_candidate",
    "loans & advances (asset)":  "journal_candidate",
    "secured loans":          "journal_candidate",
    "unsecured loans":        "journal_candidate",
    "direct expenses":        "journal_candidate",
    "indirect expenses":      "journal_candidate",
    "direct incomes":         "journal_candidate",
    "indirect incomes":       "journal_candidate",
    "sundry debtors":         "receipt",
    "sundry creditors":       "journal_candidate",
    "duties & taxes":         "journal_candidate",
    "provisions":             "journal_candidate",
    "suspense a/c":           "journal_candidate",
    "branch / divisions":     "journal_candidate",
}

def classify_transaction_by_group(party_name, ledger_parent_map, contact_type='customer'):
    """..."""
    name_lower = (party_name or '').strip().lower()
    parent_group = ledger_parent_map.get(name_lower, '')

    if parent_group in GROUP_TO_TRANSACTION_KIND:
        return GROUP_TO_TRANSACTION_KIND[parent_group]

    log.warning(f"[CLASSIFY] No PARENT group found for '{party_name}' — "
                f"using name-pattern fallback. Consider re-syncing COA.")
    BANK_PATTERNS = ['bank', 'icici', 'hdfc', 'sbi', 'axis', 'kotak', 'canara']
    CASH_PATTERNS = ['cash', 'petty cash']
    if any(p in name_lower for p in BANK_PATTERNS):
        return 'transfer'
    if any(p in name_lower for p in CASH_PATTERNS):
        return 'contra'
    return 'receipt' if contact_type == 'customer' else 'payment'
# ──────────────── END NEW MAP + FUNCTION ────────────────

# ---------------- XML PARSERS ----------------

def parse_ledgers(xml_data, ledger_type="customer"):
    ledgers = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        for ledger in root.findall(".//LEDGER"):
            name_elem = ledger.find(".//NAME")
            parent = ledger.findtext("PARENT", default="")
            email = ledger.findtext("EMAIL", default="")
            ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
            state_name = ledger.findtext("LEDSTATENAME", default="")
            country_name = ledger.findtext("COUNTRYNAME", default="")
            pincode = ledger.findtext("PINCODE", default="")
            address_elems = ledger.findall(".//ADDRESS")
            address = ", ".join([e.text.strip() for e in address_elems if e.text])

            if ledger_type == "customer" and parent.strip().lower() == "sundry debtors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent, "email": email, "address": address,
                    "ledger_mobile": ledger_mobile, "state_name": state_name,
                    "country_name": country_name, "pincode": pincode
                })
            elif ledger_type == "vendor" and parent.strip().lower() == "sundry creditors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent, "email": email, "address": address,
                    "ledger_mobile": ledger_mobile, "state_name": state_name,
                    "country_name": country_name, "pincode": pincode
                })
        log.info(f"[PARSE] {ledger_type.upper()}S: {len(ledgers)} found")
        return ledgers
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error ({ledger_type}): {e}")
        raise Exception(f"Failed to parse {ledger_type} XML from Tally.")


def parse_coa_ledgers(xml_data):
    accounts = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="Unknown")
            account_type = TALLY_TO_ZOHO_ACCOUNT_TYPE.get(parent)
            accounts.append({"account_name": name, "account_code": name, "account_type": account_type})
        log.info(f"[PARSE] COA: {len(accounts)} accounts found")
        return accounts
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error (COA): {e}")
        raise Exception("Failed to parse COA XML from Tally.")


def parse_items(xml_data):
    items = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        for item in root.findall(".//STOCKITEM"):
            name = item.findtext(".//NAME", default="Unknown")
            rate_raw = (item.findtext("RATE", default="0") or "0").strip()
            log.debug(f"[ITEM] {item.findtext('.//NAME', '')} raw rate: '{rate_raw}'")
            rate_match = re.search(r"[\d]+\.?\d*", rate_raw.replace(",", ""))
            rate = rate_match.group(0) if rate_match else "0"
            log.debug(f"[ITEM] {item.findtext('.//NAME', '')} parsed rate: '{rate}'")

            description = item.findtext("DESCRIPTION", default="")
            sku = item.findtext("PARTNUMBER", default="")
            product_type = item.findtext("PARENT", default="General")
            gst_applicable = item.findtext("GSTAPPLICABLE", default="Not Applicable")
            gst_rate = "0"
            hsn_code = ""

            gst_details_list = item.findall("GSTDETAILS.LIST")
            if gst_details_list:
                first = gst_details_list[0]
                hsn_text = first.findtext("HSN")
                if hsn_text:
                    hsn_code = hsn_text.strip()
                statewise = first.find("STATEWISEDETAILS.LIST")
                if statewise is not None:
                    rate_details = statewise.findall("RATEDETAILS.LIST")
                    igst_found = False
                    for rd in rate_details:
                        duty = rd.findtext("GSTRATEDUTYHEAD", "").strip()
                        rval = rd.findtext("GSTRATE", "").strip()
                        if duty == "IGST" and rval:
                            gst_rate = rval
                            igst_found = True
                            break
                    if not igst_found:
                        total = 0
                        for rd in rate_details:
                            duty = rd.findtext("GSTRATEDUTYHEAD", "").strip()
                            rval = rd.findtext("GSTRATE", "").strip()
                            if duty in ("CGST", "SGST/UTGST") and rval:
                                try:
                                    total += float(rval)
                                except ValueError:
                                    pass
                        if total > 0:
                            gst_rate = str(total)

            items.append({
                "name": name, "rate": rate, "description": description,
                "sku": sku, "product_type": product_type,
                "gst_applicable": gst_applicable, "gst_rate": gst_rate, "hsn_code": hsn_code
            })
        log.info(f"[PARSE] ITEMS: {len(items)} found")
        return items
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error (Items): {e}")
        raise Exception("Failed to parse item XML from Tally.")


def parse_taxes(xml_data):
    taxes = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        TAX_PARENTS = {
            "duties & taxes", "gst", "cgst", "sgst", "igst", "utgst",
            "tds payable", "tcs payable", "service tax", "vat",
        }
        GST_RATE_DEFAULTS = {
            'cgst': 9.0, 'sgst': 9.0, 'igst': 18.0,
            'cgst @5%': 5.0, 'sgst @5%': 5.0,
            'cgst @12%': 12.0, 'sgst @12%': 12.0,
            'cgst @18%': 18.0, 'sgst @18%': 18.0, 'igst @18%': 18.0,
            'cgst @28%': 28.0, 'sgst @28%': 28.0,
        }

        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="").strip()
            parent = ledger.findtext("PARENT", default="").strip()
            if parent.lower() not in TAX_PARENTS:
                continue

            name_lower = name.lower()
            if "cgst" in name_lower:
                tax_type = "CGST"
            elif "sgst" in name_lower or "utgst" in name_lower:
                tax_type = "SGST"
            elif "igst" in name_lower:
                tax_type = "IGST"
            elif "tds" in name_lower:
                tax_type = "TDS"
            elif "tcs" in name_lower:
                tax_type = "TCS"
            else:
                tax_type = "Other"

            raw_rate = (
                ledger.findtext("TAXRATE") or
                ledger.findtext("BASICRATEOFTAX") or
                ledger.findtext("RATEOFTAXATION") or
                ledger.findtext("PERCENTAGEOFTAXATION") or "0"
            ).strip()

            try:
                tax_rate = float(raw_rate)
            except ValueError:
                tax_rate = 0.0

            if tax_rate == 0.0:
                m = re.search(r'(\d+(\.\d+)?)\s*%?', name)
                if m:
                    c = float(m.group(1))
                    if 0.1 <= c <= 100:
                        tax_rate = c

            if tax_rate == 0.0:
                tax_rate = GST_RATE_DEFAULTS.get(name_lower, 0.0)

            if tax_rate == 0.0:
                log.warning(f"[PARSE] Skipping tax '{name}' — rate is 0.0")
                continue

            taxes.append({
                "tax_name": name, "ledger_name": name, "parent": parent,
                "tax_type": tax_type, "tax_rate": tax_rate, "is_active": True,
            })
        log.info(f"[PARSE] TAXES: {len(taxes)} found")
        return taxes
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error (Taxes): {e}")
        raise Exception("Failed to parse Tax XML from Tally.")


def parse_opening_balances(xml_data):
    balances = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="").strip()
            parent = ledger.findtext("PARENT", default="").strip()
            ob_raw = ledger.findtext("OPENINGBALANCE", default="0").strip()
            is_credit = "Cr" in ob_raw
            ob_clean = ob_raw.replace("Dr", "").replace("Cr", "").strip()
            try:
                amount = float(ob_clean)
            except ValueError:
                amount = 0.0
            if amount == 0.0:
                continue
            balances.append({
                "ledger_name": name, "parent": parent,
                "opening_balance": amount,
                "balance_type": "credit" if is_credit else "debit",
            })
        log.info(f"[PARSE] OPENING BALANCES: {len(balances)} found")
        return balances
    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error (Opening Balances): {e}")
        raise Exception("Failed to parse Opening Balance XML from Tally.")


def parse_all_vouchers(xml_data, from_date="", to_date="", ledger_parent_map=None):
    ledger_parent_map = ledger_parent_map or {}   # ←←← ADD THIS LINE right after the signature
    """
    Parse all vouchers from Tally Collection XML.

    BUG FIXES APPLIED:
    #1 — is_cancelled check moved to AFTER vch_no is defined (was NameError crash)
    #2 — vch_no now uses REFERENCE field (human-readable invoice number) with
         VOUCHERNUMBER as fallback. VOUCHERNUMBER alone returns '1','2','3' in
         Collection export mode, not the actual formatted invoice number.
    #4 — Expense vs payment classification now checks paid_through (cash/bank
         ledger) instead of party_name. party_name is the vendor, not cash/bank.
    #7 — grand_total for bills recomputed AFTER the purchase zero-amount fallback,
         not before, so bills with 0 initial total get the correct grand_total.
    """
    result = {
        "invoices": [], "receipts": [], "bills": [],
        "payments": [], "credit_notes": [], "vendor_credits": [],
        "journals": [], "expenses": [],
    }
    unmatched = {}

    # Build a reliable ledger_name → is_bank_or_cash lookup using Tally's own
    # PARENT classification — NOT keyword guessing on the ledger name.
    global BANK_CASH_LEDGER_SET
    BANK_CASH_LEDGER_SET = set()
    try:
        xml_coa_cache = get_tally_data(TALLY_REQUEST_XML_COA, "COA (classification cache)")
        coa_list_cache = parse_coa_ledgers(xml_coa_cache)
        for acct in coa_list_cache:
            if acct.get("account_type") in ("bank", "cash"):
                BANK_CASH_LEDGER_SET.add(acct["account_name"].strip())
        log.info(f"[PARSE] Bank/Cash ledger set built: {len(BANK_CASH_LEDGER_SET)} ledgers")
    except Exception as e:
        log.warning(f"[PARSE] Could not build bank/cash ledger set: {e}")

    global VENDOR_NAMES_CACHE
    VENDOR_NAMES_CACHE = set()
    try:
        xml_vendors_cache = get_tally_data(TALLY_REQUEST_XML_VENDORS, "VENDORS (classification cache)")
        vendor_list_cache = parse_ledgers(xml_vendors_cache, "vendor")
        VENDOR_NAMES_CACHE = {v["name"].strip() for v in vendor_list_cache}
        log.info(f"[PARSE] Vendor name set built: {len(VENDOR_NAMES_CACHE)} vendors")
    except Exception as e:
        log.warning(f"[PARSE] Could not build vendor name cache: {e}")

    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)
        all_vouchers = root.findall(".//VOUCHER")
        log.info(f"[PARSE] VOUCHERS: {len(all_vouchers)} total found in XML")

        vch_types_found = set()
        for v in all_vouchers:
            vt = (v.get("VCHTYPE") or v.findtext("VOUCHERTYPENAME", default="")).strip()
            vch_types_found.add(vt)
        log.info(f"[PARSE] Voucher types in XML: {vch_types_found}")

        for voucher in all_vouchers:
            vch_type_raw = (
                voucher.get("VCHTYPE") or
                voucher.findtext("VOUCHERTYPENAME", default="")
            ).strip()

            # Skip vouchers with no type — header/template nodes in Collection export
            if not vch_type_raw:
                log.debug(f"[VOUCHER] ⏭ Skipping voucher with empty type")
                continue

            canonical = classify_voucher(vch_type_raw)

            # date_fmt must be assigned BEFORE the resolver call (resolver uses it as fallback)
            date_raw  = voucher.findtext("DATE", default="").strip()
            date_fmt  = _format_date(date_raw)

            # ── Resolve human-readable voucher number (universal across all companies) ──
            # Different Tally companies number vouchers differently:
            #   - Some use formatted VOUCHERNUMBER  : 'GST/2024-25/001' → use as-is
            #   - Some use plain sequential numbers : '1','2','3' → prefix e.g. 'INV-1'
            #   - Some store the number in REFERENCE field (manual numbering)
            #   - Some store it in BILLALLOCATIONS.LIST.NAME
            # _resolve_voucher_number() handles all these cases automatically.
            # Prefix is set per canonical type so e.g. invoices get 'INV-1',
            # bills get 'BILL-1', receipts get 'REC-1' etc.
            type_prefix_map = {
                "sales":       "INV",
                "purchase":    "BILL",
                "receipt":     "REC",
                "payment":     "PAY",
                "credit_note": "CN",
                "debit_note":  "DN",
                "journal":     "JV",
                "contra":      "CONTRA",
            }
            prefix = type_prefix_map.get(canonical or "", "VCH")
            vch_no = _resolve_voucher_number(voucher, prefix, date_fmt)
            # ── END voucher number resolution ───────────────────────────────────────

            # ── is_cancelled check after vch_no is defined ────────────────────────
            is_cancelled = (
                voucher.get("ISCANCELLED") or
                voucher.findtext("ISCANCELLED", "")
            ).strip().lower()
            if is_cancelled in ("yes", "true", "1"):
                log.debug(f"[VOUCHER] ⏭ Skipping cancelled voucher #{vch_no}")
                continue
            # ─────────────────────────────────────────────────────────────────────
            narration = voucher.findtext("NARRATION", default="").strip()
            party_name, total_amount, is_bank_transfer = _get_voucher_amount(voucher)

            # For sales vouchers with unknown party — use Cash Customer fallback
            if party_name in [None, "", "Unknown"] and canonical == "sales":
                party_name = (
                    voucher.findtext("BASICBUYERNAME", "").strip() or
                    voucher.findtext("CONSIGNEEDETAILS.LIST/CONSIGNEENAME", "").strip() or
                    "Cash Customer"
                )

            # Tax amounts
            cgst = sgst = igst = 0.0
            tax_ledgers = []
            for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                ln = (le.findtext("LEDGERNAME") or "").strip()
                ln_lower = ln.lower()
                try:
                    amt = abs(float(le.findtext("AMOUNT") or "0.0"))
                except ValueError:
                    amt = 0.0
                if "cgst" in ln_lower:
                    cgst += amt
                    if amt > 0:
                        tax_ledgers.append({"name": ln, "amount": amt, "type": "cgst"})
                elif "sgst" in ln_lower or "utgst" in ln_lower:
                    sgst += amt
                    if amt > 0:
                        tax_ledgers.append({"name": ln, "amount": amt, "type": "sgst"})
                elif "igst" in ln_lower:
                    igst += amt
                    if amt > 0:
                        tax_ledgers.append({"name": ln, "amount": amt, "type": "igst"})

            # Line items (inventory)
            line_items = []
            for ie in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
                item_name = ie.findtext("STOCKITEMNAME", default="Item")
                qty = (ie.findtext("ACTUALQTY") or "1").strip()
                try:
                    amt = abs(float(ie.findtext("AMOUNT") or "0.0"))
                except ValueError:
                    amt = 0.0
                line_items.append({"item_name": item_name, "quantity": qty, "amount": f"{amt:.2f}"})

            # Payment mode / bill reference
            # Payment mode / bill reference — uses structural bank/cash detection
            payment_mode = "cash"
            ref_name = None
            for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                ln = (le.findtext("LEDGERNAME") or "").strip()
                if _is_cash_bank_ledger(ln):
                    payment_mode = ln
                bill_alloc = le.find(".//BILLALLOCATIONS.LIST")
                if bill_alloc is not None:
                    r = bill_alloc.findtext("NAME")
                    if r:
                        ref_name = r.strip()

            # grand_total for non-purchase types (purchase recalculates below)
            grand_total = f"{total_amount + cgst + sgst + igst:.2f}"

            # ────────────────────────────────────────────────────────────────────────
            if canonical == "sales":
                if not line_items:
                    line_items = [{"item_name": f"Sales - {party_name}", "quantity": "1", "amount": f"{total_amount:.2f}"}]
                result["invoices"].append({
                    "customer_name":  party_name,
                    "invoice_number": vch_no,
                    "invoice_date":   date_fmt,
                    "line_items":     line_items,
                    "tax_ledgers":    tax_ledgers,
                    "cgst":           f"{cgst:.2f}",
                    "sgst":           f"{sgst:.2f}",
                    "igst":           f"{igst:.2f}",
                    "total_amount":   grand_total,
                })
                log.debug(f"[VOUCHER] ✅ INVOICE #{vch_no} | {party_name} | {grand_total}")

            elif canonical == "receipt":
                kind = classify_transaction_by_group(party_name, ledger_parent_map, 'customer')   # ←←← ADD
                result["receipts"].append({
                    "receipt_number": vch_no,
                    "customer_name":  party_name,
                    "receipt_date":   date_fmt,
                    "amount":         f"{total_amount:.2f}",
                    "payment_mode":   payment_mode,
                    "agst_ref_name":  ref_name,
                    "transaction_kind": kind,   
                })
                log.debug(f"[VOUCHER] ✅ RECEIPT #{vch_no} | {party_name} | kind={kind}")

            elif canonical == "purchase":
                # ── BUG FIX #7: zero-amount fallback BEFORE grand_total ────────────
                # Original code computed grand_total at the top of the loop BEFORE
                # this fallback, so bills with 0 total got wrong grand_total.
                if total_amount == 0.0:
                    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                        try:
                            amt = float(le.findtext("AMOUNT") or "0.0")
                            if amt < 0:                         # credit side = purchase amount
                                total_amount = abs(amt)
                                break
                        except ValueError:
                            pass
                grand_total = f"{total_amount + cgst + sgst + igst:.2f}"  # recompute after fix
                # ── END FIX #7 ──────────────────────────────────────────────────────
                if not line_items:
                    line_items = [{"item_name": f"Purchase - {party_name}", "quantity": "1", "amount": f"{total_amount:.2f}"}]
                result["bills"].append({
                    "vendor_name":  party_name,
                    "bill_number":  vch_no,
                    "bill_date":    date_fmt,
                    "line_items":   line_items,
                    "tax_ledgers":  tax_ledgers,
                    "cgst":         f"{cgst:.2f}",
                    "sgst":         f"{sgst:.2f}",
                    "igst":         f"{igst:.2f}",
                    "total_amount": grand_total,
                })
                log.debug(f"[VOUCHER] ✅ BILL #{vch_no} | {party_name} | {grand_total}")

            elif canonical == "payment":
                # party_name is now reliably the real vendor/payee (never the
                # bank/cash ledger), thanks to the structural fix in
                # _get_voucher_amount(). is_bank_transfer=True only when EVERY
                # ledger leg in the voucher is genuinely a bank/cash account.

                expense_account = None
                paid_through = "Cash"

                for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                    ln = (le.findtext("LEDGERNAME") or "").strip()
                    is_party = (le.findtext("ISPARTYLEDGER") or "").strip().lower() == "yes"
                    try:
                        amt = float(le.findtext("AMOUNT") or "0.0")
                    except ValueError:
                        amt = 0.0

                    if _is_cash_bank_ledger(ln):
                        paid_through = ln
                    elif not is_party and ln != party_name and amt != 0.0:
                        # A second non-party, non-bank ledger alongside the real
                        # party ledger = a direct expense account, not a vendor bill
                        expense_account = ln

                is_known_vendor = party_name in (VENDOR_NAMES_CACHE or set())

                if is_bank_transfer:
                    result["payments"].append({
                        "payment_number": vch_no,
                        "vendor_name":    party_name,
                        "payment_date":   date_fmt,
                        "amount":         f"{total_amount:.2f}",
                        "payment_mode":   payment_mode,
                        "ref_name":       ref_name,
                        "transaction_kind": "transfer",
                    })
                    log.debug(f"[VOUCHER] ⏭ PAYMENT #{vch_no} | {party_name} | TRANSFER (bank-to-bank)")
                elif is_known_vendor:
                    # party_name IS a registered vendor → genuine vendor payment
                    result["payments"].append({
                        "payment_number": vch_no,
                        "vendor_name":    party_name,
                        "payment_date":   date_fmt,
                        "amount":         f"{total_amount:.2f}",
                        "payment_mode":   payment_mode,
                        "ref_name":       ref_name,
                        "transaction_kind": "payment",
                    })
                    log.debug(f"[VOUCHER] ✅ PAYMENT #{vch_no} | {party_name} | {total_amount:.2f}")
                else:
                    # party_name is NOT a registered vendor → it's a direct expense.
                    # Use party_name itself as the expense account if no separate
                    # expense ledger was found.
                    account_for_expense = expense_account or party_name
                    result["expenses"].append({
                        "payment_number": vch_no,
                        "payment_date":   date_fmt,
                        "account_name":   account_for_expense,
                        "paid_through":   paid_through,
                        "amount":         f"{total_amount:.2f}",
                        "narration":      narration,
                    })
                    log.debug(f"[VOUCHER] ✅ EXPENSE #{vch_no} | {account_for_expense} | {total_amount:.2f}")

            elif canonical == "credit_note":
                # ✅ ENHANCED: Try multiple fields to find the invoice reference
                invoice_ref = ''
                
                # Strategy 1: Check BILLALLOCATIONS (for linked bills/invoices)
                for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                    bill_alloc = le.find(".//BILLALLOCATIONS.LIST")
                    if bill_alloc is not None:
                        r = bill_alloc.findtext("NAME")
                        if r:
                            invoice_ref = r.strip()
                            break
                
                # Strategy 2: Check REFERENCE field (like invoices use)
                if not invoice_ref:
                    invoice_ref = voucher.findtext("REFERENCE", "").strip()
                
                # Strategy 3: Check for AGAINSTREF or similar
                if not invoice_ref:
                    invoice_ref = voucher.findtext("AGAINSTREF", "").strip()
                
                # Strategy 4: Check all ALLLEDGERENTRIES for invoice reference
                if not invoice_ref:
                    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                        ref = le.findtext("REFERENCE", "").strip()
                        if ref and ref.startswith("INV"):
                            invoice_ref = ref
                            break
                
                if not line_items:
                    line_items = [{"item_name": f"Credit - {party_name}", "quantity": "1", "amount": f"{total_amount:.2f}"}]
                
                result["credit_notes"].append({
                    "customer_name":      party_name,
                    "credit_note_number": vch_no,
                    "credit_note_date":   date_fmt,
                    "line_items":         line_items,
                    "cgst":               f"{cgst:.2f}",
                    "sgst":               f"{sgst:.2f}",
                    "total_amount":       grand_total,
                    "invoice_number":     invoice_ref,  # NOW PROPERLY EXTRACTED!
                })
                log.debug(f"[VOUCHER] ✅ CREDIT NOTE #{vch_no} | {party_name} | Invoice: {invoice_ref or 'NONE'} | {grand_total}")

            elif canonical == "debit_note":
                if not line_items:
                    line_items = [{"item_name": f"Debit - {party_name}", "quantity": "1", "amount": f"{total_amount:.2f}"}]
                result["vendor_credits"].append({
                    "vendor_name":         party_name,
                    "vendor_credit_number": vch_no,
                    "vendor_credit_date":  date_fmt,
                    "line_items":          line_items,
                    "cgst":                f"{cgst:.2f}",
                    "sgst":                f"{sgst:.2f}",
                    "total_amount":        grand_total,
                })
                log.debug(f"[VOUCHER] ✅ DEBIT NOTE #{vch_no} | {party_name} | {grand_total}")

            elif canonical == "journal":
                journal_lines = []
                for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                    ln = (le.findtext("LEDGERNAME") or "").strip()
                    try:
                        amt = float(le.findtext("AMOUNT") or "0.0")
                    except ValueError:
                        amt = 0.0
                    if ln:
                        # Tally: negative = debit, positive = credit
                        journal_lines.append({
                            "account_name": ln,
                            "debit":  f"{abs(amt):.2f}" if amt < 0 else "0.00",
                            "credit": f"{abs(amt):.2f}" if amt > 0 else "0.00",
                        })
                result["journals"].append({
                    "journal_number": vch_no,
                    "journal_date":   date_fmt,
                    "narration":      narration,
                    "lines":          journal_lines,
                    "total_amount":   f"{total_amount:.2f}",
                })
                log.debug(f"[VOUCHER] ✅ JOURNAL #{vch_no} | {len(journal_lines)} lines")

            elif canonical == "contra":
                log.debug(f"[VOUCHER] ⏭ CONTRA #{vch_no} — skipped (bank/cash transfer)")

            else:
                unmatched[vch_type_raw] = unmatched.get(vch_type_raw, 0) + 1
                log.warning(f"[VOUCHER] ⚠️ UNMATCHED type='{vch_type_raw}' #{vch_no} | {party_name}")

        # Summary
        log.info(f"[PARSE] VOUCHER SUMMARY:")
        log.info(f"  Invoices:      {len(result['invoices'])}")
        log.info(f"  Receipts:      {len(result['receipts'])}")
        log.info(f"  Bills:         {len(result['bills'])}")
        log.info(f"  Payments:      {len(result['payments'])}")
        log.info(f"  Credit Notes:  {len(result['credit_notes'])}")
        log.info(f"  Vendor Credits:{len(result['vendor_credits'])}")
        log.info(f"  Journals:      {len(result['journals'])}")
        log.info(f"  Expenses:      {len(result['expenses'])}")

        if unmatched:
            log.warning(f"[PARSE] UNMATCHED VOUCHER TYPES (add to VOUCHER_TYPE_MAP):")
            for vt, count in unmatched.items():
                log.warning(f"  '{vt}': {count} vouchers — ADD THIS TO VOUCHER_TYPE_MAP")

        return result

    except ET.ParseError as e:
        log.error(f"[PARSE] ❌ XML Parse Error (Day Book): {e}")
        with open(os.path.join(BASE_DIR, "last_raw_daybook.xml"), "w", encoding="utf-8") as f:
            f.write(xml_data)
        raise Exception("Failed to parse Day Book XML from Tally.")

# ---------------- TALLY FETCH ----------------

def get_tally_data(tally_request_xml, label="data"):
    log.info(f"[FETCH] Requesting {label} from Tally...")
    # BUG FIX #6: Day Book XML is 12MB+ — 30s timeout is too short.
    # Use 120s for Day Book, 30s for all other requests.
    timeout = 120 if label == "DAY BOOK" else 30
    try:
        response = requests.post(
            TALLY_URL,
            data=tally_request_xml.encode("utf-8"),
            timeout=timeout
        )
        response.raise_for_status()
        log.info(f"[FETCH] ✅ {label} received ({len(response.text)} chars)")
        return response.text
    except requests.exceptions.ConnectionError:
        msg = f"[FETCH] ❌ {label} — Cannot connect to Tally at {TALLY_URL}. Is Tally running?"
        log.error(msg)
        raise Exception(msg)
    except requests.exceptions.Timeout:
        msg = f"[FETCH] ❌ {label} — Tally request timed out after {timeout}s"
        log.error(msg)
        raise Exception(msg)
    except requests.exceptions.HTTPError as e:
        msg = f"[FETCH] ❌ {label} — HTTP error: {e}"
        log.error(msg)
        raise Exception(msg)
    except requests.exceptions.RequestException as e:
        msg = f"[FETCH] ❌ {label} — Unexpected error: {e}"
        log.error(msg)
        raise Exception(msg)

# ---------------- DJANGO SENDERS ----------------

def _post(url, payload, label):
    if not url:
        log.warning(f"[SEND] ⚠️ No URL for {label} — skipping")
        return False
    try:
        response = requests.post(url, json=payload, headers=auth_headers(), timeout=30)
        if response.status_code in (200, 201):
            log.info(f"[SEND] ✅ {label} sent successfully (HTTP {response.status_code})")
            return True
        else:
            log.error(f"[SEND] ❌ {label} failed — HTTP {response.status_code}: {response.text[:300]}")
            return False
    except requests.exceptions.RequestException as e:
        log.error(f"[SEND] ❌ {label} — Request error: {e}")
        return False

def send_customers_to_django(customers):
    return _post(DJANGO_API_URL_CUSTOMERS, {"ledgers": customers}, f"CUSTOMERS ({len(customers)})")

def send_vendors_to_django(vendors):
    return _post(DJANGO_API_URL_VENDORS, {"ledgers": vendors}, f"VENDORS ({len(vendors)})")

def send_coa_to_django(accounts):
    return _post(DJANGO_API_URL_ACCOUNTS, {"accounts": accounts}, f"ACCOUNTS ({len(accounts)})")

def send_items_to_django(items):
    return _post(DJANGO_API_URL_ITEMS, {"items": items}, f"ITEMS ({len(items)})")

def send_taxes_to_django(taxes):
    return _post(DJANGO_API_URL_TAXES, {"taxes": taxes}, f"TAXES ({len(taxes)})")

def send_opening_balances_to_django(balances):
    return _post(DJANGO_API_URL_OPENING_BALANCES, {"balances": balances}, f"OPENING BALANCES ({len(balances)})")

def send_invoices_to_django(invoices):
    valid = [i for i in invoices
             if i.get("customer_name") not in [None, "", "Unknown"]
             and i.get("invoice_number") not in [None, ""]
             and i.get("invoice_date")]
    skipped = len(invoices) - len(valid)
    if skipped:
        log.warning(f"[SEND] ⚠️ INVOICES: {skipped} skipped (missing customer/number/date)")
        for i in invoices:
            if (i.get("customer_name") in [None, "", "Unknown"] or
                    i.get("invoice_number") in [None, ""] or
                    not i.get("invoice_date")):
                log.warning(
                    f"[SEND] Skipped invoice detail: "
                    f"customer='{i.get('customer_name')}' | "
                    f"number='{i.get('invoice_number')}' | "
                    f"date='{i.get('invoice_date')}'"
                )
    if not valid:
        log.warning("[SEND] ⚠️ No valid invoices to send")
        return False
    return _post(DJANGO_API_URL_INVOICES, {"invoices": valid}, f"INVOICES ({len(valid)})")

def send_receipts_to_django(receipts):
    valid = [r for r in receipts
             if r.get("customer_name") not in [None, "", "Unknown"]
             and r.get("receipt_number") not in [None, ""]
             and r.get("receipt_date")]
    if not valid:
        log.warning("[SEND] ⚠️ No valid receipts to send")
        return False
    return _post(DJANGO_API_URL_RECEIPTS, {"receipts": valid}, f"RECEIPTS ({len(valid)})")

def send_bills_to_django(bills):
    valid = [b for b in bills
             if b.get("vendor_name") not in [None, "", "Unknown"]
             and b.get("bill_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid bills to send")
        return False
    return _post(DJANGO_API_URL_BILLS, {"bills": valid}, f"BILLS ({len(valid)})")

def send_payments_to_django(payments):
    valid = [p for p in payments
             if p.get("vendor_name") not in [None, "", "Unknown"]
             and p.get("payment_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid payments to send")
        return False
    return _post(DJANGO_API_URL_PAYMENTS, {"payments": valid}, f"PAYMENTS ({len(valid)})")

def send_credit_notes_to_django(credit_notes):
    valid = [c for c in credit_notes
             if c.get("customer_name") not in [None, "", "Unknown"]
             and c.get("credit_note_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid credit notes to send")
        return False
    return _post(DJANGO_API_URL_CREDIT_NOTES, {"credit_notes": valid}, f"CREDIT NOTES ({len(valid)})")

def send_vendor_credits_to_django(vendor_credits):
    valid = [v for v in vendor_credits
             if v.get("vendor_name") not in [None, "", "Unknown"]
             and v.get("vendor_credit_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid vendor credits to send")
        return False
    return _post(DJANGO_API_URL_VENDOR_CREDITS, {"vendor_credits": valid}, f"VENDOR CREDITS ({len(valid)})")

def send_journals_to_django(journals):
    valid = [j for j in journals if j.get("journal_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid journals to send")
        return False
    return _post(DJANGO_API_URL_JOURNALS, {"journals": valid}, f"JOURNALS ({len(valid)})")

def send_expenses_to_django(expenses):
    valid = [e for e in expenses
             if e.get("account_name") not in [None, "", "Unknown"]
             and e.get("payment_number") not in [None, ""]]
    if not valid:
        log.warning("[SEND] ⚠️ No valid expenses to send")
        return False
    return _post(DJANGO_API_URL_EXPENSES, {"expenses": valid}, f"EXPENSES ({len(valid)})")

# ---------------- GUI LOGIC ----------------

def sync_data():
    try:
        log.info("=" * 60)
        log.info("SYNC STARTED")
        log.info("=" * 60)

        status_label.config(text="Fetching masters from Tally...", fg="blue")
        root.update()

        xml_customers = get_tally_data(TALLY_REQUEST_XML_CUSTOMERS, "CUSTOMERS")
        customers = parse_ledgers(xml_customers, "customer")

        xml_vendors = get_tally_data(TALLY_REQUEST_XML_VENDORS, "VENDORS")
        vendors = parse_ledgers(xml_vendors, "vendor")

        xml_coa = get_tally_data(TALLY_REQUEST_XML_COA, "COA")
        accounts = parse_coa_ledgers(xml_coa)
        ledger_parent_map = build_ledger_parent_map(xml_coa)

        xml_items = get_tally_data(TALLY_REQUEST_XML_ITEMS, "ITEMS")
        items = parse_items(xml_items)

        xml_taxes = get_tally_data(TALLY_REQUEST_XML_TAXES, "TAXES")
        taxes = parse_taxes(xml_taxes)

        xml_ob = get_tally_data(TALLY_REQUEST_XML_OPENING_BALANCES, "OPENING BALANCES")
        opening_balances = parse_opening_balances(xml_ob)

        from_date = from_date_picker.get_date().strftime("%Y%m%d")
        to_date   = to_date_picker.get_date().strftime("%Y%m%d")
        log.info(f"[SYNC] Date range: {from_date} → {to_date}")

        status_label.config(text="Fetching transactions from Tally...", fg="blue")
        root.update()

        xml_daybook = get_tally_data(get_daybook_xml(from_date, to_date), "DAY BOOK")
        all_vouchers = parse_all_vouchers(xml_daybook, from_date, to_date, ledger_parent_map)   
        invoices       = all_vouchers["invoices"]
        receipts       = all_vouchers["receipts"]
        bills          = all_vouchers["bills"]
        payments       = all_vouchers["payments"]
        credit_notes   = all_vouchers["credit_notes"]
        vendor_credits = all_vouchers["vendor_credits"]
        journals       = all_vouchers["journals"]
        expenses       = all_vouchers["expenses"]

        status_label.config(text="Sending to Django...", fg="blue")
        root.update()

        if customers:        send_customers_to_django(customers)
        if vendors:          send_vendors_to_django(vendors)
        if accounts:         send_coa_to_django(accounts)
        if items:            send_items_to_django(items)
        if taxes:            send_taxes_to_django(taxes)
        if opening_balances: send_opening_balances_to_django(opening_balances)
        if invoices:         send_invoices_to_django(invoices)
        if receipts:         send_receipts_to_django(receipts)
        if bills:            send_bills_to_django(bills)
        if payments:         send_payments_to_django(payments)
        if credit_notes:     send_credit_notes_to_django(credit_notes)
        if vendor_credits:   send_vendor_credits_to_django(vendor_credits)
        if journals:         send_journals_to_django(journals)
        if expenses:         send_expenses_to_django(expenses)

        log.info("=" * 60)
        log.info("SYNC COMPLETE")
        log.info("=" * 60)

        messagebox.showinfo("Success", f"Sync complete!\n\nFetched:\n"
                            f"  Invoices: {len(invoices)}\n"
                            f"  Bills: {len(bills)}\n"
                            f"  Receipts: {len(receipts)}\n"
                            f"  Payments: {len(payments)}\n"
                            f"  Credit Notes: {len(credit_notes)}\n"
                            f"  Vendor Credits: {len(vendor_credits)}\n"
                            f"  Journals: {len(journals)}\n"
                            f"  Expenses: {len(expenses)}\n\n"
                            f"Log saved to: {log_file}")
        status_label.config(text="✅ Sync complete!", fg="green")

    except Exception as e:
        error_details = traceback.format_exc()
        log.error(f"[SYNC] ❌ SYNC FAILED:\n{error_details}")
        messagebox.showerror("Sync Failed", f"{str(e)}\n\nCheck log file:\n{log_file}")
        status_label.config(text=f"❌ {str(e)}", fg="red")

# ---- TEMPORARY TEST — remove after verification ----
if __name__ == "__main__" and "--test-collection" in sys.argv:
    xml = get_tally_data(get_daybook_xml("20240401", "20250331"), "DAY BOOK TEST")
    with open("test_collection_output.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    import xml.etree.ElementTree as ET
    root_test = ET.fromstring(clean_xml(xml))
    vouchers_test = root_test.findall(".//VOUCHER")
    print(f"Total vouchers via Collection: {len(vouchers_test)}")
    types_test = set(v.findtext("VOUCHERTYPENAME", "") for v in vouchers_test)
    print(f"Types: {types_test}")
    sys.exit(0)
# ---- END TEMPORARY TEST ----

# ---------------- GUI SETUP ----------------

root = tk.Tk()
root.title("Tally to Django Sync Agent")
root.geometry("420x380")
root.resizable(False, False)

title_label = tk.Label(root, text="Tally → Django Sync", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

username_var = tk.StringVar()
password_var = tk.StringVar()

from_date_picker = DateEntry(root, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
to_date_picker   = DateEntry(root, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')

tk.Label(root, text="Username").pack()
tk.Entry(root, textvariable=username_var).pack()
tk.Label(root, text="Password").pack()
tk.Entry(root, textvariable=password_var, show="*").pack()
tk.Label(root, text="From Date").pack()
from_date_picker.pack()
tk.Label(root, text="To Date").pack()
to_date_picker.pack()

def login_and_sync():
    username = username_var.get()
    password = password_var.get()
    if not username or not password:
        messagebox.showwarning("Missing Fields", "Username and password are required.")
        return
    if not get_token(username, password):
        messagebox.showerror("Login Failed", "Invalid credentials or server error.")
        return
    sync_data()

sync_btn = tk.Button(root, text="Login & Sync", command=login_and_sync,
                     font=("Arial", 12), bg="green", fg="white")
sync_btn.pack(pady=20)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

log_label = tk.Label(root, text=f"Log: {log_file}", font=("Arial", 7), fg="gray")
log_label.pack(side="bottom", pady=2)

footer = tk.Label(root, text="Tally2Books Sync Agent v2.0", font=("Arial", 8), fg="gray")
footer.pack(side="bottom")

root.mainloop()