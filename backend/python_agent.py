import tkinter as tk
from tkinter import messagebox
from unittest import result
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

# ---------------- CONFIG ----------------

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
AUTH_TOKEN = None

DEFAULT_CONFIG = {
    "tally_url": "http://localhost:9000",
    "auth_url": "http://localhost:8000/api/generate_token_agent/",
    "django_api_url": "http://localhost:8000/api/users/ledgers/",
    "django_url_vendors": "http://localhost:8000/api/users/vendors/",
    "django_url_accounts": "http://localhost:8000/api/users/accounts/",
    "django_url_items": "http://localhost:8000/api/users/items/",
    "django_url_invoices": "http://localhost:8000/api/users/invoices/",
    "django_url_receipts": "http://localhost:8000/api/users/receipts/",
    "django_url_taxes": "http://localhost:8000/api/users/taxes/",
    "django_url_bills": "http://localhost:8000/api/users/bills/",
    "django_url_payments": "http://localhost:8000/api/users/payments/",
    "django_url_credit_notes": "http://localhost:8000/api/users/credit-notes/",
    "django_url_vendor_credits": "http://localhost:8000/api/users/vendor-credits/",
    "django_url_journals": "http://localhost:8000/api/users/journals/",
    "django_url_opening_balances": "http://localhost:8000/api/users/opening-balances/",
    "django_url_expenses": "http://localhost:8000/api/users/expenses/",
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

# ---------------- ITEM XML HELPERS ----------------

def get_all_item_names_xml():
    """Fetch just names of all stock items first."""
    return """<ENVELOPE>
  <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>Stock Items</ID></HEADER>
  <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
    <TDL><TDLMESSAGE>
      <COLLECTION NAME="Stock Items" ISMODIFY="No">
        <TYPE>StockItem</TYPE>
        <FETCH>NAME</FETCH>
      </COLLECTION>
    </TDLMESSAGE></TDL>
  </DESC></BODY>
</ENVELOPE>"""


def get_single_item_xml(item_name):
    """Fetch a single stock item with full GST details using Object export."""
    # Escape XML special characters in item name
    safe_name = (item_name
                 .replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace("'", "&apos;")
                 .replace('"', "&quot;"))
    return f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Object</TYPE>
    <SUBTYPE>StockItem</SUBTYPE>
    <ID>{safe_name}</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
    </DESC>
  </BODY>
</ENVELOPE>"""

# ---------------- DYNAMIC XML BUILDER ----------------

def get_daybook_xml(from_date, to_date):
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

def _resolve_voucher_number(voucher, prefix, date_fmt=""):
    vch_no    = (voucher.findtext("VOUCHERNUMBER") or "").strip()
    reference = (voucher.findtext("REFERENCE")     or "").strip()
    master_id = (voucher.findtext("MASTERID")      or "").strip()
    num_style = (voucher.findtext("NUMBERINGSTYLE") or "").strip().lower()

    if reference:
        return reference

    if vch_no and not vch_no.isdigit():
        return vch_no

    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
        for ba in le.findall(".//BILLALLOCATIONS.LIST"):
            name = (ba.findtext("NAME") or "").strip()
            if name and name != vch_no:
                return name

    if vch_no and vch_no.isdigit():
        return f"{prefix}-{vch_no}"

    if master_id:
        return f"{prefix}-M{master_id}"

    return f"{prefix}-{date_fmt.replace('-', '')}"


def _format_date(date_raw):
    date_raw = (date_raw or "").strip()
    try:
        if len(date_raw) == 8 and date_raw.isdigit():
            return f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}"
    except Exception:
        pass
    return date_raw

def _get_voucher_amount(voucher):
    party_name = (
        voucher.findtext("PARTYLEDGERNAME") or
        voucher.findtext("BASICBUYERNAME") or
        "Unknown"
    ).strip()

    total_amount = 0.0

    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
        is_party = (le.findtext("ISPARTYLEDGER") or "").strip().lower() == "yes"
        try:
            amt = abs(float(le.findtext("AMOUNT") or "0.0"))
        except ValueError:
            amt = 0.0
        if is_party and amt > 0:
            total_amount = amt
            break

    if total_amount == 0.0:
        for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ln = (le.findtext("LEDGERNAME") or "").strip()
            try:
                amt = abs(float(le.findtext("AMOUNT") or "0.0"))
            except ValueError:
                amt = 0.0
            if ln == party_name and amt > 0:
                total_amount = amt
                break

    if total_amount == 0.0:
        for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            try:
                amt = abs(float(le.findtext("AMOUNT") or "0.0"))
            except ValueError:
                amt = 0.0
            if amt > total_amount:
                total_amount = amt

    return party_name, total_amount

# ---------------- VOUCHER TYPE CLASSIFICATION ----------------

VOUCHER_TYPE_MAP = {
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
    "purchase": "purchase",
    "gst purchase": "purchase",
    "purchase invoice": "purchase",
    "tax purchase invoice": "purchase",
    "purchase - tax invoice": "purchase",
    "import invoice": "purchase",
    "purchase order": "purchase",
    "receipt": "receipt",
    "receipt voucher": "receipt",
    "payment": "payment",
    "payment voucher": "payment",
    "credit note": "credit_note",
    "credit note voucher": "credit_note",
    "sales return": "credit_note",
    "debit note": "debit_note",
    "debit note voucher": "debit_note",
    "purchase return": "debit_note",
    "journal": "journal",
    "journal voucher": "journal",
    "contra": "contra",
}

def classify_voucher(vch_type_raw):
    return VOUCHER_TYPE_MAP.get(vch_type_raw.strip().lower())

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
    """
    Two-step approach:
    1. Parse item names from collection XML
    2. Fetch each item individually using Object export for full GST/HSN details
    """
    items = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        # Step 1: Get all item names from the collection response
        item_names = []
        for item in root.findall(".//STOCKITEM"):
            name = item.findtext(".//NAME", default="").strip()
            if name and name.lower() != "unknown":
                item_names.append(name)

        log.info(f"[ITEMS] Found {len(item_names)} items — fetching GST/HSN details individually...")

        # Step 2: Fetch each item individually for full GST details
        for name in item_names:
            try:
                item_xml = get_tally_data(get_single_item_xml(name), f"ITEM:{name}")
                item_root = ET.fromstring(clean_xml(item_xml))
                item_elem = item_root.find(".//STOCKITEM")
                if item_elem is None:
                    log.warning(f"[ITEM] No STOCKITEM element found for '{name}' — skipping")
                    continue

                # Rate
                rate_raw = (item_elem.findtext("RATE") or "0").strip()
                rate_match = re.search(r"[\d]+\.?\d*", rate_raw.replace(",", ""))
                rate = rate_match.group(0) if rate_match else "0"

                # Basic fields
                description  = item_elem.findtext("DESCRIPTION") or ""
                sku          = item_elem.findtext("PARTNUMBER") or ""
                product_type = item_elem.findtext("PARENT") or "General"
                gst_applicable = item_elem.findtext("GSTAPPLICABLE") or "Not Applicable"

                # Type of supply
                type_of_supply_raw = (
                    item_elem.findtext("TYPEOFGSTSUPPLY") or
                    item_elem.findtext("TYPEOFSUPPLY") or
                    item_elem.findtext("SUPPLYTYPE") or ""
                )
                type_of_supply = "Unknown"
                if type_of_supply_raw:
                    s = type_of_supply_raw.lower().strip()
                    if "goods" in s and "service" in s:
                        type_of_supply = "Goods & Services"
                    elif "goods" in s:
                        type_of_supply = "Goods"
                    elif "service" in s:
                        type_of_supply = "Services"

                # HSN code and GST rate from full object details
                hsn_code = ""
                gst_rate = "0"

                for gst_detail in item_elem.findall(".//GSTDETAILS.LIST"):
                    # Try multiple possible HSN field names
                    hsn = (
                        gst_detail.findtext("HSN") or
                        gst_detail.findtext("HSNCODE") or
                        gst_detail.findtext("HSNDETAILS") or
                        ""
                    )
                    if hsn.strip():
                        hsn_code = hsn.strip()

                    # Extract GST rate from statewise details
                    for statewise in gst_detail.findall(".//STATEWISEDETAILS.LIST"):
                        for rate_detail in statewise.findall(".//RATEDETAILS.LIST"):
                            duty_head = (rate_detail.findtext("GSTRATEDUTYHEAD") or "").strip()
                            rate_val  = (rate_detail.findtext("GSTRATE") or "").strip()
                            if duty_head == "IGST" and rate_val:
                                gst_rate = rate_val
                                break

                log.info(f"[ITEM] {name} → HSN: '{hsn_code}' | GST: {gst_rate}% | Supply: {type_of_supply}")

                items.append({
                    "name":           name,
                    "rate":           rate,
                    "description":    description,
                    "sku":            sku,
                    "product_type":   product_type,
                    "type_of_supply": type_of_supply,
                    "gst_applicable": gst_applicable,
                    "gst_rate":       gst_rate,
                    "hsn_code":       hsn_code,
                })

            except Exception as e:
                log.warning(f"[ITEM] ⚠️ Failed to fetch details for '{name}': {e}")
                # Still add the item with empty HSN so it's not lost
                items.append({
                    "name":           name,
                    "rate":           "0",
                    "description":    "",
                    "sku":            "",
                    "product_type":   "General",
                    "type_of_supply": "Unknown",
                    "gst_applicable": "Not Applicable",
                    "gst_rate":       "0",
                    "hsn_code":       "",
                })
                continue

        log.info(f"[ITEMS] ✅ Parsed {len(items)} items with HSN codes")
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


def parse_all_vouchers(xml_data, from_date="", to_date=""):
    result = {
        "invoices": [], "receipts": [], "bills": [],
        "payments": [], "credit_notes": [], "vendor_credits": [],
        "journals": [], "expenses": [],
    }
    unmatched = {}

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

            if not vch_type_raw:
                log.debug(f"[VOUCHER] ⏭ Skipping voucher with empty type")
                continue

            canonical = classify_voucher(vch_type_raw)

            date_raw  = voucher.findtext("DATE", default="").strip()
            date_fmt  = _format_date(date_raw)

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

            is_cancelled = (
                voucher.get("ISCANCELLED") or
                voucher.findtext("ISCANCELLED", "")
            ).strip().lower()
            if is_cancelled in ("yes", "true", "1"):
                log.debug(f"[VOUCHER] ⏭ Skipping cancelled voucher #{vch_no}")
                continue

            narration = voucher.findtext("NARRATION", default="").strip()
            party_name, total_amount = _get_voucher_amount(voucher)

            if party_name in [None, "", "Unknown"] and canonical == "sales":
                party_name = (
                    voucher.findtext("BASICBUYERNAME", "").strip() or
                    voucher.findtext("CONSIGNEEDETAILS.LIST/CONSIGNEENAME", "").strip() or
                    "Cash Customer"
                )

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

            line_items = []
            for ie in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
                item_name = ie.findtext("STOCKITEMNAME", default="Item")
                qty = (ie.findtext("ACTUALQTY") or "1").strip()
                try:
                    amt = abs(float(ie.findtext("AMOUNT") or "0.0"))
                except ValueError:
                    amt = 0.0
                line_items.append({"item_name": item_name, "quantity": qty, "amount": f"{amt:.2f}"})

            payment_mode = "cash"
            ref_name = None
            cash_bank_kw = ["bank", "cash", "hdfc", "sbi", "icici", "axis", "kotak", "yes bank", "canara"]
            for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                ln = (le.findtext("LEDGERNAME") or "").strip()
                if any(k in ln.lower() for k in cash_bank_kw):
                    payment_mode = ln
                bill_alloc = le.find(".//BILLALLOCATIONS.LIST")
                if bill_alloc is not None:
                    r = bill_alloc.findtext("NAME")
                    if r:
                        ref_name = r.strip()

            grand_total = f"{total_amount + cgst + sgst + igst:.2f}"

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
                result["receipts"].append({
                    "receipt_number": vch_no,
                    "customer_name":  party_name,
                    "receipt_date":   date_fmt,
                    "amount":         f"{total_amount:.2f}",
                    "payment_mode":   payment_mode,
                    "agst_ref_name":  ref_name,
                })
                log.debug(f"[VOUCHER] ✅ RECEIPT #{vch_no} | {party_name} | {total_amount:.2f}")

            elif canonical == "purchase":
                if total_amount == 0.0:
                    for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                        try:
                            amt = float(le.findtext("AMOUNT") or "0.0")
                            if amt < 0:
                                total_amount = abs(amt)
                                break
                        except ValueError:
                            pass
                grand_total = f"{total_amount + cgst + sgst + igst:.2f}"
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
                expense_account = None
                paid_through = "Cash"

                for le in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                    ln = (le.findtext("LEDGERNAME") or "").strip()
                    ln_lower = ln.lower()
                    is_party = (le.findtext("ISPARTYLEDGER") or "").strip().lower() == "yes"
                    try:
                        amt = float(le.findtext("AMOUNT") or "0.0")
                    except ValueError:
                        amt = 0.0

                    if any(k in ln_lower for k in cash_bank_kw):
                        paid_through = ln
                    elif not is_party and not any(k in ln_lower for k in cash_bank_kw) and amt != 0.0:
                        # Only treat as expense if ledger name matches known expense patterns
                        # Vendor names (Sundry Creditors) should NOT be classified as expense accounts
                        expense_keywords = [
                            "expense", "charges", "freight", "transport", "salary",
                            "wages", "rent", "electricity", "telephone", "postage",
                            "printing", "stationery", "repairs", "maintenance",
                            "insurance", "interest", "bank charges", "audit",
                            "accounting", "legal", "professional", "advertisement",
                            "travelling", "conveyance", "loading", "unloading",
                            "rates", "taxes", "duties", "gst paid", "tds",
                             "od interest", "commission"
                    ]
                    is_expense_ledger = any(kw in ln_lower for kw in expense_keywords)
                    if is_expense_ledger:
                        expense_account = ln
        

                # If there's a party name that isn't a bank/cash account, it's a vendor payment
                is_vendor_payment = (
                    party_name not in [None, "", "Unknown", "Cash Customer"] and
                    not any(k in party_name.lower() for k in cash_bank_kw)
                )

                # Only classify as expense if NO vendor party is involved
                if expense_account and not is_vendor_payment:
                    result["expenses"].append({
                        "payment_number": vch_no,
                        "payment_date":   date_fmt,
                        "account_name":   expense_account,
                        "paid_through":   paid_through,
                        "amount":         f"{total_amount:.2f}",
                        "narration":      narration,
                    })
                    log.debug(f"[VOUCHER] ✅ EXPENSE #{vch_no} | {expense_account} | {total_amount:.2f}")
                else:
                    result["payments"].append({
                        "payment_number": vch_no,
                        "vendor_name":    party_name,
                        "payment_date":   date_fmt,
                        "amount":         f"{total_amount:.2f}",
                        "payment_mode":   payment_mode,
                        "ref_name":       ref_name,
                    })
                    log.debug(f"[VOUCHER] ✅ PAYMENT #{vch_no} | {party_name} | {total_amount:.2f}")

            elif canonical == "credit_note":
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
                })
                log.debug(f"[VOUCHER] ✅ CREDIT NOTE #{vch_no} | {party_name} | {grand_total}")

            elif canonical == "debit_note":
                if not line_items:
                    line_items = [{"item_name": f"Debit - {party_name}", "quantity": "1", "amount": f"{total_amount:.2f}"}]
                result["vendor_credits"].append({
                    "vendor_name":          party_name,
                    "vendor_credit_number": vch_no,
                    "vendor_credit_date":   date_fmt,
                    "line_items":           line_items,
                    "cgst":                 f"{cgst:.2f}",
                    "sgst":                 f"{sgst:.2f}",
                    "total_amount":         grand_total,
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

        # Two-step item fetch: names first, then individual GST details
        xml_items = get_tally_data(get_all_item_names_xml(), "ITEMS")
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
        all_vouchers = parse_all_vouchers(xml_daybook, from_date, to_date)

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

        messagebox.showinfo("Success", f"""Sync complete!

Masters:
  Customers:        {len(customers)}
  Vendors:          {len(vendors)}
  Accounts:         {len(accounts)}
  Items:            {len(items)}
  Taxes:            {len(taxes)}
  Opening Balances: {len(opening_balances)}

Transactions:
  Invoices:         {len(invoices)}
  Bills:            {len(bills)}
  Receipts:         {len(receipts)}
  Payments:         {len(payments)}
  Credit Notes:     {len(credit_notes)}
  Vendor Credits:   {len(vendor_credits)}
  Journals:         {len(journals)}
  Expenses:         {len(expenses)}

Log saved to: {log_file}""")

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

def sync_items_only():
    username = username_var.get()
    password = password_var.get()
    if not username or not password:
        messagebox.showwarning("Missing Fields", "Username and password are required.")
        return
    if not get_token(username, password):
        messagebox.showerror("Login Failed", "Invalid credentials or server error.")
        return
    try:
        status_label.config(text="Fetching items from Tally...", fg="blue")
        root.update()
        # Two-step: get names first, then fetch each individually
        xml_items = get_tally_data(get_all_item_names_xml(), "ITEMS")
        items = parse_items(xml_items)
        if items:
            send_items_to_django(items)
        log.info(f"[SYNC] Items only sync complete — {len(items)} items")
        messagebox.showinfo("Success", f"Items sync complete!\n\nItems fetched: {len(items)}\n\nLog: {log_file}")
        status_label.config(text=f"✅ {len(items)} items synced!", fg="green")
    except Exception as e:
        error_details = traceback.format_exc()
        log.error(f"[SYNC] ❌ Items sync failed:\n{error_details}")
        messagebox.showerror("Failed", str(e))
        status_label.config(text=f"❌ {str(e)}", fg="red")

items_btn = tk.Button(root, text="Sync Items Only", command=sync_items_only,
                      font=("Arial", 10), bg="#1c64f2", fg="white")
items_btn.pack(pady=4)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

log_label = tk.Label(root, text=f"Log: {log_file}", font=("Arial", 7), fg="gray")
log_label.pack(side="bottom", pady=2)

footer = tk.Label(root, text="Tally2Books Sync Agent v2.0", font=("Arial", 8), fg="gray")
footer.pack(side="bottom")

root.mainloop()