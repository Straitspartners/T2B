import xml.etree.ElementTree as ET
import re

XML_FILE = "D:/tally-to-books/backend/last_raw_tally.xml"

print("\n" + "="*100)
print("🔍 ANALYZING TALLY XML - ITEMS")
print("="*100)

try:
    with open(XML_FILE, 'r', encoding='utf-8') as f:
        xml_data = f.read()
    
    xml_data = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_data)
    root = ET.fromstring(xml_data)
    items = root.findall(".//STOCKITEM")
    
    print(f"\n📦 Found {len(items)} items\n")
    
    if len(items) > 0:
        first = items[0]
        name = first.findtext('.//NAME', 'N/A')
        print(f"First Item: {name}\n")
        print("All fields:")
        
        for child in first:
            text = (child.text or '')[:60]
            print(f"  {child.tag:<35} = {text}")

except Exception as e:
    print(f"Error: {e}")
