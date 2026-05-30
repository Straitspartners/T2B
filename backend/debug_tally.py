import requests, re
import xml.etree.ElementTree as ET

xml = """<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>voucher register</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>20260401</SVFROMDATE>
          <SVTODATE>20260430</SVTODATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

r = requests.post("http://localhost:9000", data=xml)
raw = re.sub(r'&#\d+;', '', r.text)
raw = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', raw)

root = ET.fromstring(raw)

for voucher in root.findall(".//VOUCHER"):
    if voucher.findtext("VOUCHERTYPENAME", "").strip().lower() != "sales":
        continue
    print("=== ALL VOUCHER FIELDS ===")
    for child in voucher:
        if child.text and child.text.strip():
            print(f"  {child.tag}: {child.text.strip()}")
    print("\n=== LEDGER ENTRIES ===")
    for le in voucher.findall(".//LEDGERENTRIES.LIST"):
        for child in le:
            if child.text and child.text.strip():
                print(f"  {child.tag}: {child.text.strip()}")