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

CONFIG_PATH = "config.json"
AUTH_TOKEN = None

DEFAULT_CONFIG = {
    "tally_url": "http://localhost:9000",
    "django_api_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/ledgers/",
    "django_url_vendors": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/vendors/",
    "auth_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/generate_token_agent/"  # Django token endpoint
}

# DEFAULT_CONFIG = {
#     "tally_url": "http://localhost:9000",
#     "django_api_url": "http://127.0.0.1:8000/api/users/ledgers/",
#     "django_url_vendors": "http://127.0.0.1:8000/api/users/vendors/",
#     "auth_url": "http://127.0.0.1:8000/api/generate_token_agent/"  # Django token endpoint
# }

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
# DJANGO_API_URL = config["django_api_url"]
AUTH_URL = config["auth_url"]
DJANGO_API_URL_CUSTOMERS =config["django_api_url"]
DJANGO_API_URL_VENDORS =config["django_url_vendors"]

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

# ---------------- TALLY REQUEST ----------------

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
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE</FETCH>
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
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE</FETCH>
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

# TALLY_REQUEST_XML_SALES_VOUCHERS = """
# <ENVELOPE>
#   <HEADER>
#     <VERSION>1</VERSION>
#     <TALLYREQUEST>Export</TALLYREQUEST>
#     <TYPE>Collection</TYPE>
#     <ID>Sales Vouchers</ID>
#   </HEADER>
#   <BODY>
#     <DESC>
#       <STATICVARIABLES>
#         <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
#         <EXPLODEFLAG>Yes</EXPLODEFLAG>
#         <SVFROMDATE>20240101</SVFROMDATE>
#         <SVTODATE>20251231</SVTODATE>
#       </STATICVARIABLES>
#       <TDL>
#         <TDLMESSAGE>
#           <COLLECTION NAME="Sales Vouchers" ISMODIFY="No">
#             <TYPE>Voucher</TYPE>
#             <FILTER>IsSales</FILTER>
#             <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST</FETCH>
#           </COLLECTION>
#           <SYSTEM TYPE="Formulae" NAME="IsSales">
#             $VoucherTypeName = "Sales"
#           </SYSTEM>
#         </TDLMESSAGE>
#       </TDL>
#     </DESC>
#   </BODY>
# </ENVELOPE>
# """

# TALLY_REQUEST_XML_RECEIPTS = """
# <ENVELOPE>
#   <HEADER>
#     <VERSION>1</VERSION>
#     <TALLYREQUEST>Export</TALLYREQUEST>
#     <TYPE>Collection</TYPE>
#     <ID>Receipt Vouchers</ID>
#   </HEADER>
#   <BODY>
#     <DESC>
#       <STATICVARIABLES>
#         <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
#         <EXPLODEFLAG>Yes</EXPLODEFLAG>
#         <SVFROMDATE>20240101</SVFROMDATE>
#         <SVTODATE>20251231</SVTODATE>
#       </STATICVARIABLES>
#       <TDL>
#         <TDLMESSAGE>
#           <COLLECTION NAME="Receipt Vouchers" ISMODIFY="No">
#             <TYPE>Voucher</TYPE>
#             <FILTER>IsReceipt</FILTER>
#             <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
#           </COLLECTION>
#           <SYSTEM TYPE="Formulae" NAME="IsReceipt">
#             $VoucherTypeName = "Receipt"
#           </SYSTEM>
#         </TDLMESSAGE>
#       </TDL>
#     </DESC>
#   </BODY>
# </ENVELOPE>
# """

def get_sales_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Sales Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Sales Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsSales</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsSales">
                $VoucherTypeName = "Sales"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """

def get_receipt_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Receipt Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Receipt Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsReceipt</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsReceipt">
                $VoucherTypeName = "Receipt"
              </SYSTEM>
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


def parse_bank_ledgers(xml_data):
    import xml.etree.ElementTree as ET
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


# def send_banks_to_django(banks):
#     try:
#         headers = {"Authorization": f"Token {AUTH_TOKEN}"}
#         response = requests.post(DJANGO_API_URL_BANKS, json={"ledgers": banks}, headers=headers)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error sending banks to Django: {e}")
#         raise Exception("Failed to send bank ledger data to Django server.")




# TALLY_TO_ZOHO_ACCOUNT_TYPE = {
#     "Bank Accounts": "Bank",
#     "Bank OCC A/c": "Bank",
#     "Bank OD A/c": "Loan",
#     "Branch / Divisions": "Other Current Asset",
#     "Capital Account": "Equity",
#     "Cash-in-Hand": "Cash and Cash Equivalents",
#     "Current Assets": "Other Current Asset",
#     "Current Liabilities": "Current Liability",
#     "Deposits (Asset)": "Deposits",
#     "Direct Expenses": "Cost of Goods Sold (COGS)",
#     "Direct Incomes": "Revenue",
#     "Duties & Taxes": "Tax Payable",
#     "Expenses (Direct)": "Cost of Goods Sold (COGS)",
#     "Expenses (Indirect)": "Other Expense",
#     "Fixed Assets": "Fixed Asset",
#     "Income (Direct)": "Revenue",
#     "Income (Indirect)": "Other Income",
#     "Indirect Expenses": "Other Expense",
#     "Indirect Incomes": "Other Income",
#     "Investments": "Investments",
#     "Loans & Advances (Asset)": "Other Current Asset",
#     "Loans (Liability)": "Loan",
#     "Misc. Expenses (ASSET)": "Prepaid Expense",
#     "Provisions": "Other Current Liability",
#     "Purchase Accounts": "Cost of Goods Sold",
#     "Reserves & Surplus": "Equity",
#     "Retained Earnings": "Retained Earnings",
#     "Sales Accounts": "Revenue",
#     "Secured Loans": "Loan",
#     "Stock-in-Hand": "Inventory Asset",
#     "Sundry Creditors": "Accounts Payable",
#     "Sundry Debtors": "Accounts Receivable",
#     "Suspense A/c": "Suspense Account",
#     "Unsecured Loans": "Loan",
# }
TALLY_TO_ZOHO_ACCOUNT_TYPE = {
    "Bank Accounts": "bank", ##Bank
    "Bank OCC A/c": "bank",  ##Bank
    "Bank OD A/c": "bank",   ##N
    "Branch / Divisions": "other_liability",  
    "Capital Account": "equity",
    "Cash-in-Hand": "cash",
    "Current Assets": "other_current_asset", 
    "Current Liabilities": "other_current_liability",
    "Deposits (Asset)": "other_current_asset",
    "Direct Expenses": "expense",
    "Direct Incomes": "income",
    "Duties & Taxes": "other_current_asset",  #other current asset
    "Expenses (Direct)": "expense",
    "Expenses (Indirect)": "other_expense",
    "Fixed Assets": "fixed_asset",
    "Income (Direct)": "income",
    "Income (Indirect)": "other_income",
    "Indirect Expenses": "other_expense",
    "Indirect Incomes": "other_income",
    "Investments": "other_current_asset",  #other_current_asset
    "Loans & Advances (Asset)": "other_current_asset", ##Doubt
    "Loans (Liability)": "long_term_liability", ##doubt me
    "Misc. Expenses (ASSET)": "other_asset",
    "Provisions": "other_current_liability",
    "Purchase Accounts": "cost_of_goods_sold",
    "Reserves & Surplus": "equity",
    "Retained Earnings": "income", 
    "Sales Accounts": "income",
    "Secured Loans": "other_liability", 
    "Stock-in-Hand": "cost_of_goods_sold", # --
    "Sundry Creditors": "accounts_payable",
    "Sundry Debtors": "accounts_receivable",
    "Suspense A/c": "other_liability",
    "Unsecured Loans": "loans_and_borrowing", #--
}
# ---------------- XML PARSER ----------------

def clean_xml(xml_string):
    xml_string = re.sub(r'&#\d+;', '', xml_string)  # Remove numeric character references
    xml_string = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_string)  # Remove control chars
    return xml_string


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
                "account_code": name,  # assuming Tally name is code for now
                "account_type": account_type,
            })

        return accounts

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (COA): {e}")
        raise Exception("Failed to parse COA XML from Tally.")
    
import xml.etree.ElementTree as ET
import logging

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

            # Initialize GST fields
            gst_rate = "0"
            hsn_code = ""

            # Extract GST details
            gst_details_list = item.findall("GSTDETAILS.LIST")
            if gst_details_list:
                first_gst_detail = gst_details_list[0]

                # Extract HSN
                hsn_text = first_gst_detail.findtext("HSN")
                if hsn_text:
                    hsn_code = hsn_text.strip()

                # Navigate to nested STATEWISEDETAILS
                statewise_details = first_gst_detail.find("STATEWISEDETAILS.LIST")
                if statewise_details is not None:
                    rate_details_list = statewise_details.findall("RATEDETAILS.LIST")

                    # Prefer IGST rate if available
                    igst_found = False
                    for rate_detail in rate_details_list:
                        duty_head = rate_detail.findtext("GSTRATEDUTYHEAD", "").strip()
                        rate_val = rate_detail.findtext("GSTRATE", "").strip()

                        if duty_head == "IGST" and rate_val:
                            gst_rate = rate_val
                            igst_found = True
                            break  # Found IGST, exit loop

                    # If IGST not found, sum CGST + SGST
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

            # Append parsed item
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



from collections import defaultdict

def parse_sales_vouchers(xml_data):
    invoices = defaultdict(lambda: {
        "customer_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "items": [],
        "cgst": 0.0,
        "sgst": 0.0,
        "total_amount": 0.0
    })

    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        inv_no = voucher.findtext("VOUCHERNUMBER", default="Unknown")
        ledger_entry = voucher.find(".//LEDGERENTRIES.LIST")
        customer = ledger_entry.findtext("LEDGERNAME", default="Unknown") if ledger_entry is not None else "Unknown"
        date_raw = voucher.findtext("DATE", default="")
        date = f"{date_raw[6:8]}-{date_raw[4:6]}-{date_raw[0:4]}" if len(date_raw) == 8 else date_raw

        key = (inv_no, customer, date)

        invoice = invoices[key]
        invoice["customer_name"] = customer
        invoice["invoice_number"] = inv_no
        invoice["invoice_date"] = date

        # Line items
        for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
            item_name = item.findtext("STOCKITEMNAME", default="")
            qty = item.findtext("ACTUALQTY", default="")
            amt = float(item.findtext("AMOUNT", default="0.0"))

            invoice["items"].append({
                "item_name": item_name,
                "quantity": qty.strip(),
                "amount": f"{amt:.2f}"
            })
            invoice["total_amount"] += amt

        # Taxes (CGST, SGST)
        for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", "").lower()
            amt = float(ledger.findtext("AMOUNT", default="0.0"))

            if "cgst" in ledger_name:
                invoice["cgst"] += abs(amt)
            elif "sgst" in ledger_name:
                invoice["sgst"] += abs(amt)

    # Format totals as string with 2 decimals
    return [
        {
            **inv,
            "cgst": f"{inv['cgst']:.2f}",
            "sgst": f"{inv['sgst']:.2f}",
            "total_amount": f"{(inv['total_amount'] + inv['cgst'] + inv['sgst']):.2f}"
        }
        for inv in invoices.values()
    ]





def parse_receipts(xml_data):
    receipts = []

    # Clean and parse XML
    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)
    for voucher in root.findall(".//VOUCHER"):
        receipt_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()

        try:
            receipt_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            receipt_date = date_str

        total_amount = 0.0
        customer_name = "Unknown"
        payment_mode = "Unknown"
        cur_balance = None
        ref_name = None

        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            amt_str = ledger.findtext("AMOUNT", default="0.0").strip()

            try:
                amt = float(amt_str)
            except:
                amt = 0.0

            # Payment mode: bank/cash
            if "bank" in ledger_name.lower() or "cash" in ledger_name.lower():
                payment_mode = ledger_name
            else:
                # Customer details
                customer_name = ledger_name
                total_amount = amt

                # Get current balance
                balance_tags = ["CURRENTBALANCE", "LEDGERCLOSINGBALANCE", "CLOSINGBALANCE", "OPENINGBALANCE", "BALANCE"]
                for tag in balance_tags:
                    balance_str = ledger.findtext(tag)
                    if balance_str:
                        try:
                            cur_balance = float(balance_str)
                            break
                        except:
                            continue

                # Get Agst Ref Name only from the customer ledger
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

def send_customers_to_django(customers):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(DJANGO_API_URL_CUSTOMERS, json={"ledgers": customers}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending customers to Django: {e}")
        raise Exception("Failed to send customers data to server.")

def send_vendors_to_django(vendors):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(DJANGO_API_URL_VENDORS, json={"ledgers": vendors}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending vendors to Django: {e}")
        raise Exception("Failed to send vendors data to server.")

def send_coa_to_django(accounts):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post("https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/accounts/", json={"accounts": accounts}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending COA to Django: {e}")
        raise Exception("Failed to send COA data to server.")
    
def send_items_to_django(items):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post("https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/items/", json={"items": items}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending items to Django: {e}")
        raise Exception("Failed to send items to server.")
    
import logging

def send_invoices_to_django(invoices):
    try:
        valid_invoices = []
        for inv in invoices:
            if (
                inv.get("customer_name") not in [None, "", "Unknown"]
                and inv.get("invoice_number") not in [None, "", "Unknown"]
                and inv.get("invoice_date")
                and inv.get("items") and isinstance(inv.get("items"), list) and len(inv.get("items")) > 0
            ):
                valid_invoices.append(inv)
            else:
                print(f"⚠️ Skipping invalid invoice: {inv}")

        if not valid_invoices:
            raise Exception("No valid invoices to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/invoices/",
            json={"invoices": valid_invoices},
            headers=headers
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())  # <-- Show detailed validation error
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

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/receipts/",
            json={"receipts": valid_receipts},
            headers=headers
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

        # Fetch customers
        xml_customers = get_tally_data(TALLY_REQUEST_XML_CUSTOMERS)
        customers = parse_ledgers(xml_customers, ledger_type="customer")

        # Fetch and process bank accounts
        # xml_banks = get_tally_data(TALLY_REQUEST_XML_BANK_ACCOUNTS)
        # banks = parse_bank_ledgers(xml_banks)

        # Fetch vendors
        xml_vendors = get_tally_data(TALLY_REQUEST_XML_VENDORS)
        vendors = parse_ledgers(xml_vendors, ledger_type="vendor")
        for bank in vendors:
            print(json.dumps(bank, indent=2))

        # Chart of Accounts
        xml_coa = get_tally_data(TALLY_REQUEST_XML_COA)
        accounts = parse_coa_ledgers(xml_coa)

        # Items
        xml_items = get_tally_data(TALLY_REQUEST_XML_ITEMS)
        items = parse_items(xml_items)
        # for item in items:
        #   print("\nFetched Items:")
        
        #   print(json.dumps(item, indent=2))

        from_date = from_date_picker.get_date().strftime("%Y%m%d")
        to_date = to_date_picker.get_date().strftime("%Y%m%d")

        # Invoices
        xml_sales = get_tally_data(get_sales_voucher_xml(from_date, to_date))
        invoices = parse_sales_vouchers(xml_sales)
        from datetime import datetime
        for invoice in invoices:
          try:
            if invoice.get("invoice_date"):
              invoice["invoice_date"] = datetime.strptime(invoice["invoice_date"], "%d-%m-%Y").strftime("%Y-%m-%d")
          except Exception as e:
              # print(f"⚠️ Date formatting failed for invoice: {invoice.get('invoice_number')}, error: {e}")
              invoice["invoice_date"] = None
        
        print("\nFetched Invoices:")
        for invoice in invoices:
          print(json.dumps(invoice, indent=2))

        # if not customers and not vendors:
        #     messagebox.showwarning("No Data", "No customers or vendors found in Tally.")
        #     status_label.config(text="No ledgers found.", fg="orange")
        #     return

        xml_receipts=get_tally_data(get_receipt_voucher_xml(from_date, to_date))
        receipts=parse_receipts(xml_receipts)
        print("\nFetched Receipts:")
        for receipt in receipts:
          print(json.dumps(receipt, indent=2))

        # if banks:
        #   print("\nFetched Bank Ledgers:")
        #   for bank in banks:
        #     print(json.dumps(bank, indent=2))
        #   send_banks_to_django(banks)

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

        
        status_label.config(text="Syncing data to Django...", fg="blue")
        messagebox.showinfo("Success", "Customers and Vendors synced successfully!")
        status_label.config(text="✅ Sync complete!", fg="green")

    except Exception as e:
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

sync_btn = tk.Button(root, text="Login & Sync", command=login_and_sync, font=("Arial", 12), bg="green", fg="white")
sync_btn.pack(pady=20)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

footer = tk.Label(root, text="v1.0 - Developed by Your Company", font=("Arial", 8), fg="gray")
footer.pack(side="bottom", pady=5)

root.mainloop()




# Installers :

# pip install requests
# pip install pyinstaller
# pyinstaller --onefile --windowed python_agent.py
# pip install tkcalendar

