import tkinter as tk
from tkinter import messagebox
import requests
import xml.etree.ElementTree as ET
import json
import os
import logging
import re
from tkcalendar import DateEntry

# ---------------- CONFIG ----------------

import sys
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
    "django_url_receipts": "http://localhost:8000/api/users/receipts/"
}

# ---------------- LOGGING ----------------

logging.basicConfig(
    filename='sync_gui.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ---------------- CONFIG LOADER ----------------

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    else:
        with open(CONFIG_PATH, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG

config = load_config()
TALLY_URL = config["tally_url"]
AUTH_URL = config["auth_url"]
DJANGO_API_URL_CUSTOMERS = config["django_api_url"]
DJANGO_API_URL_VENDORS = config["django_url_vendors"]
DJANGO_API_URL_ACCOUNTS = config.get("django_url_accounts", DEFAULT_CONFIG["django_url_accounts"])
DJANGO_API_URL_ITEMS = config.get("django_url_items", DEFAULT_CONFIG["django_url_items"])
DJANGO_API_URL_INVOICES = config.get("django_url_invoices", DEFAULT_CONFIG["django_url_invoices"])
DJANGO_API_URL_RECEIPTS = config.get("django_url_receipts", DEFAULT_CONFIG["django_url_receipts"])

# ---------------- TOKEN HANDLER ----------------

def get_token(username, password):
    global AUTH_TOKEN
    try:
        response = requests.post(AUTH_URL, data={"username": username, "password": password})
        response.raise_for_status()
        token_data = response.json()
        AUTH_TOKEN = token_data.get("token")
        return True if AUTH_TOKEN else False
    except requests.exceptions.RequestException as e:
        logging.error(f"Login failed: {e}")
        return False

def auth_headers():
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

# ---------------- TALLY REQUEST XML ----------------

TALLY_REQUEST_XML_CUSTOMERS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Customer Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Customer Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsSundryDebtor</FILTER>
            <FETCH>NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE</FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsSundryDebtor">
             $Parent = "Sundry Debtors"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_VENDORS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Vendor Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Vendor Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsSundryCreditor</FILTER>
            <FETCH>NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE</FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsSundryCreditor">
             $Parent = "Sundry Creditors"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_COA = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>All Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="All Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FETCH>NAME, PARENT</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_ITEMS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Stock Items</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Stock Items" ISMODIFY="No">
            <TYPE>StockItem</TYPE>
            <FETCH>NAME, RATE, DESCRIPTION, PARTNUMBER, PARENT, GSTAPPLICABLE, GSTDETAILS.RATE, GSTDETAILS.HSN</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_BANK_ACCOUNTS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Bank Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Bank Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsBankAccount</FILTER>
            <FETCH>
              NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE,
              BANKALLOCATIONS.BANKNAME, BANKALLOCATIONS.BRANCHNAME, BANKALLOCATIONS.IFSCODE,
              BANKALLOCATIONS.ACCOUNTNUMBER, BANKALLOCATIONS.BSRCODE
            </FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsBankAccount">
            $Parent = "Bank Accounts"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

# ---------------- DYNAMIC XML BUILDERS ----------------

def get_sales_voucher_xml(from_date, to_date):
    """
    ✅ FIX: Use Export Data / voucher register instead of TDL Collection.
    TDL Collection filter doesn't work in TallyPrime EDU version.
    """
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>voucher register</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>{from_date}</SVFROMDATE>
          <SVTODATE>{to_date}</SVTODATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

def get_receipt_voucher_xml(from_date, to_date):
    """
    ✅ FIX: Same fix applied to receipts — use Export Data instead of TDL Collection.
    """
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>voucher register</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>{from_date}</SVFROMDATE>
          <SVTODATE>{to_date}</SVTODATE>
          <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
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
    "Duties & Taxes": "other_current_asset",
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
            website = ledger.findtext("WEBSITE", default="")
            ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
            state_name = ledger.findtext("LEDSTATENAME", default="")
            country_name = ledger.findtext("COUNTRYNAME", default="")
            pincode = ledger.findtext("PINCODE", default="")

            address_elems = ledger.findall(".//ADDRESS")
            address_lines = [elem.text.strip() for elem in address_elems if elem.text]
            address = ", ".join(address_lines)

            if ledger_type == "customer" and parent.strip().lower() == "sundry debtors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent,
                    "email": email,
                    "address": address,
                    "ledger_mobile": ledger_mobile,
                    "website": website,
                    "state_name": state_name,
                    "country_name": country_name,
                    "pincode": pincode
                })
            elif ledger_type == "vendor" and parent.strip().lower() == "sundry creditors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent,
                    "email": email,
                    "address": address,
                    "ledger_mobile": ledger_mobile,
                    "website": website,
                    "state_name": state_name,
                    "country_name": country_name,
                    "pincode": pincode
                })

        return ledgers

    except ET.ParseError as e:
        logging.error(f"XML Parse Error: {e}")
        with open("last_raw_tally.xml", "w", encoding="utf-8") as file:
            file.write(xml_data)
        raise Exception("Failed to parse Tally XML response.")


def parse_coa_ledgers(xml_data):
    accounts = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="Unknown")
            account_type = TALLY_TO_ZOHO_ACCOUNT_TYPE.get(parent)

            accounts.append({
                "account_name": name,
                "account_code": name,
                "account_type": account_type,
            })

        return accounts

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (COA): {e}")
        raise Exception("Failed to parse COA XML from Tally.")


def parse_items(xml_data):
    items = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for item in root.findall(".//STOCKITEM"):
            name = item.findtext(".//NAME", default="Unknown")
            rate = item.findtext("RATE", default="0")
            description = item.findtext("DESCRIPTION", default="")
            sku = item.findtext("PARTNUMBER", default="")
            product_type = item.findtext("PARENT", default="General")
            gst_applicable = item.findtext("GSTAPPLICABLE", default="Not Applicable")

            gst_rate = "0"
            hsn_code = ""

            gst_details_list = item.findall("GSTDETAILS.LIST")
            if gst_details_list:
                first_gst_detail = gst_details_list[0]
                hsn_text = first_gst_detail.findtext("HSN")
                if hsn_text:
                    hsn_code = hsn_text.strip()

                statewise_details = first_gst_detail.find("STATEWISEDETAILS.LIST")
                if statewise_details is not None:
                    rate_details_list = statewise_details.findall("RATEDETAILS.LIST")
                    igst_found = False
                    for rate_detail in rate_details_list:
                        duty_head = rate_detail.findtext("GSTRATEDUTYHEAD", "").strip()
                        rate_val = rate_detail.findtext("GSTRATE", "").strip()
                        if duty_head == "IGST" and rate_val:
                            gst_rate = rate_val
                            igst_found = True
                            break
                    if not igst_found:
                        total = 0
                        for rate_detail in rate_details_list:
                            duty_head = rate_detail.findtext("GSTRATEDUTYHEAD", "").strip()
                            rate_val = rate_detail.findtext("GSTRATE", "").strip()
                            if duty_head in ("CGST", "SGST/UTGST") and rate_val:
                                try:
                                    total += float(rate_val)
                                except ValueError:
                                    pass
                        if total > 0:
                            gst_rate = str(total)

            items.append({
                "name": name,
                "rate": rate,
                "description": description,
                "sku": sku,
                "product_type": product_type,
                "gst_applicable": gst_applicable,
                "gst_rate": gst_rate,
                "hsn_code": hsn_code
            })

        return items

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (Items): {e}")
        raise Exception("Failed to parse item XML from Tally.")


def parse_bank_ledgers(xml_data):
    ledgers = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="")
            email = ledger.findtext("EMAIL", default="")
            website = ledger.findtext("WEBSITE", default="")
            ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
            state_name = ledger.findtext("LEDSTATENAME", default="")
            country_name = ledger.findtext("COUNTRYNAME", default="")
            pincode = ledger.findtext("PINCODE", default="")

            address_elems = ledger.findall(".//ADDRESS")
            address_lines = [elem.text.strip() for elem in address_elems if elem.text]
            address = ", ".join(address_lines)

            bank_name = ledger.findtext(".//BANKALLOCATIONS.BANKNAME", default="")
            branch_name = ledger.findtext(".//BANKALLOCATIONS.BRANCHNAME", default="")
            ifsc_code = ledger.findtext(".//BANKALLOCATIONS.IFSCODE", default="")
            account_number = ledger.findtext(".//BANKALLOCATIONS.ACCOUNTNUMBER", default="")
            bsr_code = ledger.findtext(".//BANKALLOCATIONS.BSRCODE", default="")

            ledgers.append({
                "name": name,
                "parent": parent,
                "email": email,
                "address": address,
                "ledger_mobile": ledger_mobile,
                "website": website,
                "state_name": state_name,
                "country_name": country_name,
                "pincode": pincode,
                "bank_name": bank_name,
                "branch_name": branch_name,
                "ifsc_code": ifsc_code,
                "account_number": account_number,
                "bsr_code": bsr_code
            })

        return ledgers

    except ET.ParseError as e:
        logging.error(f"XML Parse Error in Bank Ledgers: {e}")
        with open("last_raw_bank_ledgers.xml", "w", encoding="utf-8") as file:
            file.write(xml_data)
        raise Exception("Failed to parse Tally Bank Ledger XML.")


from collections import defaultdict

def parse_sales_vouchers(xml_data):
    """
    ✅ FIXED parser for TallyPrime EDU version.

    Key fixes:
    1. Reads customer from PARTYLEDGERNAME at voucher level (not nested ledger entry)
    2. Reads total amount from LEDGERENTRIES.LIST > AMOUNT (largest positive value)
    3. Items made optional — EDU version strips ALLINVENTORYENTRIES detail
       so we create a single line item from the voucher total
    4. CGST/SGST read from LEDGERENTRIES where ledger name contains 'cgst'/'sgst'
    5. Validation no longer requires items list to be non-empty
    """
    invoices = []

    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for voucher in root.findall(".//VOUCHER"):
            vch_type = voucher.findtext("VOUCHERTYPENAME", default="").strip()

            # Only process Sales vouchers
            if vch_type.lower() != "sales":
                continue

            inv_no = voucher.findtext("VOUCHERNUMBER", default="").strip()
            date_raw = voucher.findtext("DATE", default="").strip()

            # ✅ Fix 1: Read customer from PARTYLEDGERNAME at voucher level
            customer = (
                voucher.findtext("PARTYLEDGERNAME")
                or voucher.findtext("BASICBUYERNAME")
                or "Unknown"
            ).strip()

            # Format date: 20260401 → 2026-04-01
            try:
                invoice_date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw
            except Exception:
                invoice_date = date_raw

            # ✅ Fix 2: Read amounts from LEDGERENTRIES.LIST
            total_amount = 0.0
            cgst = 0.0
            sgst = 0.0

            for le in voucher.findall(".//LEDGERENTRIES.LIST"):
                ledger_name = (le.findtext("LEDGERNAME") or "").lower()
                is_party_ledger = (le.findtext("ISPARTYLEDGER") or "").strip().lower() == "yes"
                try:
                    amt = float(le.findtext("AMOUNT") or "0.0")
                except ValueError:
                    amt = 0.0

                if "cgst" in ledger_name:
                    cgst += abs(amt)
                elif "sgst" in ledger_name or "utgst" in ledger_name:
                    sgst += abs(amt)
                elif is_party_ledger:
                    # ✅ Fix 3: Party ledger entry has negative amount (receivable)
                    # Use its absolute value as the invoice total
                    total_amount = abs(amt)

            # If total still 0, fallback to largest absolute amount
            if total_amount == 0.0:
                for le in voucher.findall(".//LEDGERENTRIES.LIST"):
                    try:
                        amt = abs(float(le.findtext("AMOUNT") or "0.0"))
                        total_amount = max(total_amount, amt)
                    except ValueError:
                        pass

            # ✅ Fix 4: Items optional — create a placeholder if EDU strips them
            items = []
            for ie in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
                item_name = ie.findtext("STOCKITEMNAME", default="Item")
                qty = (ie.findtext("ACTUALQTY") or "1").strip()
                try:
                    amt = float(ie.findtext("AMOUNT") or "0.0")
                except ValueError:
                    amt = 0.0
                items.append({
                    "item_name": item_name,
                    "quantity": qty,
                    "amount": f"{abs(amt):.2f}"
                })

            # If no items found (EDU limitation), create one from total
            if not items:
                items = [{
                    "item_name": "Sales Item",
                    "quantity": "1",
                    "amount": f"{total_amount:.2f}"
                }]

            grand_total = total_amount + cgst + sgst

            invoices.append({
                "customer_name": customer,
                "invoice_number": inv_no,
                "invoice_date": invoice_date,
                "items": items,
                "cgst": f"{cgst:.2f}",
                "sgst": f"{sgst:.2f}",
                "total_amount": f"{grand_total:.2f}"
            })

        return invoices

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (Invoices): {e}")
        with open("last_raw_invoices.xml", "w", encoding="utf-8") as file:
            file.write(xml_data)
        raise Exception("Failed to parse Sales Voucher XML from Tally.")


def parse_receipts(xml_data):
    receipts = []

    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        vch_type = voucher.findtext("VOUCHERTYPENAME", default="").strip()
        if vch_type.lower() != "receipt":
            continue

        receipt_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()

        try:
            receipt_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except Exception:
            receipt_date = date_str

        # ✅ Read customer from PARTYLEDGERNAME at voucher level
        customer_name = (
            voucher.findtext("PARTYLEDGERNAME")
            or voucher.findtext("BASICBUYERNAME")
            or "Unknown"
        ).strip()

        total_amount = 0.0
        payment_mode = "Unknown"
        cur_balance = None
        ref_name = None

        for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
            ledger_name = (ledger.findtext("LEDGERNAME") or "").strip()
            amt_str = ledger.findtext("AMOUNT") or "0.0"
            try:
                amt = float(amt_str)
            except Exception:
                amt = 0.0

            if "bank" in ledger_name.lower() or "cash" in ledger_name.lower():
                payment_mode = ledger_name
            elif amt != 0.0:
                total_amount = amt

            bill_alloc = ledger.find(".//BILLALLOCATIONS.LIST")
            if bill_alloc is not None:
                ref_name = bill_alloc.findtext("NAME", default=None)

        receipts.append({
            "receipt_number": receipt_number,
            "customer_name": customer_name,
            "receipt_date": receipt_date,
            "amount": f"{abs(total_amount):.2f}",
            "payment_mode": payment_mode,
            "cur_balance": f"{cur_balance:.2f}" if cur_balance is not None else None,
            "agst_ref_name": ref_name
        })

    return receipts

# ---------------- TALLY SYNC ----------------

def get_tally_data(tally_request_xml):
    try:
        response = requests.post(TALLY_URL, data=tally_request_xml)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Tally connection failed: {e}")
        raise Exception("Could not connect to Tally. Is it running and listening on port 9000?")

# ---------------- DJANGO SENDERS ----------------

def send_customers_to_django(customers):
    try:
        response = requests.post(DJANGO_API_URL_CUSTOMERS, json={"ledgers": customers}, headers=auth_headers())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending customers to Django: {e}")
        raise Exception("Failed to send customers data to server.")

def send_vendors_to_django(vendors):
    try:
        response = requests.post(DJANGO_API_URL_VENDORS, json={"ledgers": vendors}, headers=auth_headers())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending vendors to Django: {e}")
        raise Exception("Failed to send vendors data to server.")

def send_coa_to_django(accounts):
    try:
        response = requests.post(DJANGO_API_URL_ACCOUNTS, json={"accounts": accounts}, headers=auth_headers())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending COA to Django: {e}")
        raise Exception("Failed to send COA data to server.")

def send_items_to_django(items):
    try:
        response = requests.post(DJANGO_API_URL_ITEMS, json={"items": items}, headers=auth_headers())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending items to Django: {e}")
        raise Exception("Failed to send items to server.")

def send_invoices_to_django(invoices):
    try:
        valid_invoices = []
        for inv in invoices:
            # ✅ Fix 5: items no longer required to be non-empty for validation
            if (
                inv.get("customer_name") not in [None, "", "Unknown"]
                and inv.get("invoice_number") not in [None, "", "Unknown"]
                and inv.get("invoice_date")
            ):
                valid_invoices.append(inv)
            else:
                print(f"⚠️ Skipping invalid invoice: {inv}")

        if not valid_invoices:
            raise Exception("No valid invoices to send.")

        response = requests.post(
            DJANGO_API_URL_INVOICES,
            json={"invoices": valid_invoices},
            headers=auth_headers()
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())
            raise Exception("Failed to send invoices to server.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending invoices to Django: {e}")
        raise Exception("Failed to send invoices to server.")

def send_receipts_to_django(receipts):
    try:
        valid_receipts = []
        for receipt in receipts:
            if (
                receipt.get("customer_name") not in [None, "", "Unknown"]
                and receipt.get("receipt_number") not in [None, "", "Unknown"]
                and receipt.get("receipt_date")
            ):
                valid_receipts.append(receipt)
            else:
                print(f"⚠️ Skipping invalid receipt: {receipt}")

        if not valid_receipts:
            raise Exception("No valid receipts to send.")

        response = requests.post(
            DJANGO_API_URL_RECEIPTS,
            json={"receipts": valid_receipts},
            headers=auth_headers()
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending receipts to Django: {e}")
        raise

# ---------------- GUI LOGIC ----------------

def sync_data():
    try:
        status_label.config(text="Connecting to Tally...", fg="blue")
        root.update()

        xml_customers = get_tally_data(TALLY_REQUEST_XML_CUSTOMERS)
        customers = parse_ledgers(xml_customers, ledger_type="customer")

        xml_vendors = get_tally_data(TALLY_REQUEST_XML_VENDORS)
        vendors = parse_ledgers(xml_vendors, ledger_type="vendor")

        xml_coa = get_tally_data(TALLY_REQUEST_XML_COA)
        accounts = parse_coa_ledgers(xml_coa)

        xml_items = get_tally_data(TALLY_REQUEST_XML_ITEMS)
        items = parse_items(xml_items)

        from_date = from_date_picker.get_date().strftime("%Y%m%d")
        to_date = to_date_picker.get_date().strftime("%Y%m%d")

        xml_sales = get_tally_data(get_sales_voucher_xml(from_date, to_date))
        invoices = parse_sales_vouchers(xml_sales)

        from datetime import datetime
        for invoice in invoices:
            try:
                if invoice.get("invoice_date"):
                    invoice["invoice_date"] = datetime.strptime(
                        invoice["invoice_date"], "%Y-%m-%d"
                    ).strftime("%Y-%m-%d")
            except Exception:
                pass

        print("\nFetched Invoices:")
        for invoice in invoices:
            print(json.dumps(invoice, indent=2))

        xml_receipts = get_tally_data(get_receipt_voucher_xml(from_date, to_date))
        receipts = parse_receipts(xml_receipts)

        print("\nFetched Receipts:")
        for receipt in receipts:
            print(json.dumps(receipt, indent=2))

        status_label.config(text="Syncing data to Django...", fg="blue")
        root.update()

        if customers:
            send_customers_to_django(customers)
        if vendors:
            send_vendors_to_django(vendors)
        if accounts:
            send_coa_to_django(accounts)
        if items:
            send_items_to_django(items)
        if invoices:
            send_invoices_to_django(invoices)
        if receipts:
            send_receipts_to_django(receipts)

        messagebox.showinfo("Success", "All data synced successfully!")
        status_label.config(text="✅ Sync complete!", fg="green")

    except Exception as e:
        logging.error(f"Sync failed: {e}")
        messagebox.showerror("Error", str(e))
        status_label.config(text=f"❌ {str(e)}", fg="red")


# ---------------- GUI SETUP ----------------

root = tk.Tk()
root.title("Tally to Django Sync Agent")
root.geometry("400x360")
root.resizable(False, False)

title_label = tk.Label(root, text="Tally → Django Sync", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

username_var = tk.StringVar()
password_var = tk.StringVar()

from_date_picker = DateEntry(root, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
to_date_picker = DateEntry(root, width=12, background='darkblue',
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

footer = tk.Label(root, text="v1.0 - Developed by Your Company",
                  font=("Arial", 8), fg="gray")
footer.pack(side="bottom", pady=5)

root.mainloop()