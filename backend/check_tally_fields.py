import requests
import xml.etree.ElementTree as ET
import re

def clean_xml(xml_string):
    xml_string = re.sub(r'&#\d+;', '', xml_string)
    xml_string = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_string)
    return xml_string

# Fetch full year — no date filter so we don't miss anything
tally_xml = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Test</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVFROMDATE>20240401</SVFROMDATE>
        <SVTODATE>20250331</SVTODATE>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Test" ISMODIFY="No">
            <TYPE>Voucher</TYPE>
            <FETCH>
              DATE,
              VOUCHERTYPENAME,
              VOUCHERNUMBER,
              REFERENCE,
              ALTEREDON,
              VOUCHERTYPEALIAS,
              MASTERID,
              VOUCHERKEY,
              NUMBERINGSTYLE,
              VOUCHERNUMBERSERIES,
              PARTYLEDGERNAME,
              BASICBUYERNAME,
              ALLLEDGERENTRIES.LIST.LEDGERNAME,
              ALLLEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME,
              ALLLEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.BILLTYPE
            </FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""

print("Connecting to Tally...")
try:
    resp = requests.post(
        "http://localhost:9000",
        data=tally_xml.encode("utf-8"),
        timeout=120
    )
    resp.raise_for_status()
    print(f"Response size : {len(resp.text)} chars")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

root = ET.fromstring(clean_xml(resp.text))
vouchers = root.findall(".//VOUCHER")
print(f"Total vouchers : {len(vouchers)}\n")

# Collect all SALES vouchers
sales = [v for v in vouchers
         if "sales" in (v.findtext("VOUCHERTYPENAME") or v.get("VCHTYPE") or "").lower()]

print(f"Total GST SALES vouchers : {len(sales)}")
print()

# Show numbering style distribution
styles = {}
for v in sales:
    style = v.findtext("NUMBERINGSTYLE", "UNKNOWN").strip()
    styles[style] = styles.get(style, 0) + 1
print("NUMBERINGSTYLE distribution:")
for s, c in sorted(styles.items(), key=lambda x: -x[1]):
    print(f"  {s!r}: {c} vouchers")
print()

# Show first 5 sales vouchers — all key fields
print("=" * 60)
print("FIRST 5 SALES VOUCHERS — FULL FIELD DUMP")
print("=" * 60)
for i, v in enumerate(sales[:5]):
    vnum        = v.findtext("VOUCHERNUMBER", "").strip()
    reference   = v.findtext("REFERENCE", "").strip()
    masterid    = v.findtext("MASTERID", "").strip()
    voucherkey  = v.findtext("VOUCHERKEY", "").strip()
    num_style   = v.findtext("NUMBERINGSTYLE", "").strip()
    num_series  = v.findtext("VOUCHERNUMBERSERIES", "").strip()
    party       = v.findtext("PARTYLEDGERNAME", "").strip()
    date        = v.findtext("DATE", "").strip()

    print(f"\nVOUCHER #{i+1}")
    print(f"  DATE              : {date!r}")
    print(f"  PARTYLEDGERNAME   : {party!r}")
    print(f"  VOUCHERNUMBER     : {vnum!r}")
    print(f"  REFERENCE         : {reference!r}")
    print(f"  MASTERID          : {masterid!r}")
    print(f"  VOUCHERKEY        : {voucherkey!r}")
    print(f"  NUMBERINGSTYLE    : {num_style!r}")
    print(f"  VOUCHERNUMBERSERIES: {num_series!r}")

    # Bill allocations
    bill_names = []
    for le in v.findall(".//ALLLEDGERENTRIES.LIST"):
        for ba in le.findall(".//BILLALLOCATIONS.LIST"):
            name = ba.findtext("NAME", "").strip()
            btype = ba.findtext("BILLTYPE", "").strip()
            if name:
                bill_names.append(f"{name!r} (type={btype!r})")
    print(f"  BILL ALLOC NAMES  : {bill_names if bill_names else '(none)'}")

# Also check what bill allocation names look like — they sometimes store formatted numbers
print()
print("=" * 60)
print("BILL ALLOCATION NAMES SAMPLE (first 20 non-empty)")
print("=" * 60)
found = 0
for v in sales:
    for le in v.findall(".//ALLLEDGERENTRIES.LIST"):
        for ba in le.findall(".//BILLALLOCATIONS.LIST"):
            name = ba.findtext("NAME", "").strip()
            if name:
                party = v.findtext("PARTYLEDGERNAME", "").strip()
                vnum  = v.findtext("VOUCHERNUMBER", "").strip()
                print(f"  VOUCHERNUMBER={vnum!r} | PARTY={party!r} | BILLALLOC={name!r}")
                found += 1
                if found >= 20:
                    break
        if found >= 20:
            break
    if found >= 20:
        break

if found == 0:
    print("  (no bill allocations found in any sales voucher)")