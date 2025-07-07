#!/usr/bin/env python3
"""Verify Hostfact compatibility fixes."""

import sys
from pathlib import Path
import re

def compare_xml_files():
    """Compare old and new XML files to show improvements."""
    
    old_file = Path("test_invoice.xml")
    new_file = Path("test_hostfact_fixed.xml")
    
    if not old_file.exists():
        print("❌ Original test file not found. Run: ./pdf2ubl.py test")
        return False
    
    if not new_file.exists():
        print("❌ Fixed test file not found. Run: ./pdf2ubl.py test --output test_hostfact_fixed.xml")
        return False
    
    print("🔍 Comparing XML files for Hostfact compatibility...")
    print("=" * 60)
    
    # Read both files
    with open(old_file, 'r', encoding='utf-8') as f:
        old_content = f.read()
    
    with open(new_file, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    # Check decimal formatting
    print("\n1. DECIMAL FORMATTING:")
    old_decimals = re.findall(r'>(\d+\.\d+)<', old_content)
    new_decimals = re.findall(r'>(\d+\.\d+)<', new_content)
    
    print(f"   Old format examples: {old_decimals[:3]}")
    print(f"   New format examples: {new_decimals[:3]}")
    
    # Check for excessive decimals
    old_long_decimals = [d for d in old_decimals if len(d.split('.')[1]) > 2]
    new_long_decimals = [d for d in new_decimals if len(d.split('.')[1]) > 2]
    
    if old_long_decimals and not new_long_decimals:
        print("   ✅ Fixed: Removed excessive decimal places")
    elif new_long_decimals:
        print("   ❌ Still has excessive decimals:", new_long_decimals[:3])
    else:
        print("   ✅ Decimal formatting is consistent")
    
    # Check VAT/BTW codes
    print("\n2. VAT/BTW CODES:")
    old_btw = re.findall(r'<cbc:ID>([^<]+)</cbc:ID>', old_content)
    new_vat = re.findall(r'<cbc:ID>([^<]+)</cbc:ID>', new_content)
    
    old_btw_in_tax = 'BTW' in old_content
    new_vat_standard = 'VAT' in new_content and 'Standard rate' in new_content
    
    print(f"   Old uses BTW: {old_btw_in_tax}")
    print(f"   New uses VAT standard: {new_vat_standard}")
    
    if old_btw_in_tax and new_vat_standard:
        print("   ✅ Fixed: Changed from Dutch BTW to international VAT codes")
    
    # Check tax scheme names
    print("\n3. TAX SCHEME NAMES:")
    old_tax_names = re.findall(r'<cbc:Name>([^<]*(?:BTW|Omzetbelasting)[^<]*)</cbc:Name>', old_content)
    new_tax_names = re.findall(r'<cbc:Name>([^<]*(?:VAT|Standard)[^<]*)</cbc:Name>', new_content)
    
    print(f"   Old tax names: {set(old_tax_names)}")
    print(f"   New tax names: {set(new_tax_names)}")
    
    if old_tax_names and not any('BTW' in name or 'Omzetbelasting' in name for name in new_tax_names):
        print("   ✅ Fixed: Standardized tax scheme names")
    
    # File size comparison
    print("\n4. FILE SIZE:")
    old_size = len(old_content)
    new_size = len(new_content)
    print(f"   Old file: {old_size:,} characters")
    print(f"   New file: {new_size:,} characters")
    print(f"   Difference: {new_size - old_size:+,} characters")
    
    print("\n" + "=" * 60)
    return True

def check_hostfact_requirements():
    """Check specific Hostfact requirements."""
    
    print("\n📋 HOSTFACT COMPATIBILITY CHECKLIST:")
    print("=" * 60)
    
    new_file = Path("test_hostfact_fixed.xml")
    if not new_file.exists():
        print("❌ Fixed test file not found")
        return False
    
    with open(new_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("UBL 2.1 namespace", "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" in content),
        ("Proper CustomizationID", "urn:cen.eu:en16931:2017" in content),
        ("Standard VAT codes", "<cbc:ID>VAT</cbc:ID>" in content),
        ("2-decimal amounts", not re.search(r'>\d+\.\d{3,}<', content)),
        ("Invoice ID present", "<cbc:ID>" in content and not "<cbc:ID></cbc:ID>" in content),
        ("Issue date present", "<cbc:IssueDate>" in content),
        ("Currency code", "<cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>" in content),
        ("Supplier party", "<cac:AccountingSupplierParty>" in content),
        ("Customer party", "<cac:AccountingCustomerParty>" in content),
        ("Tax totals", "<cac:TaxTotal>" in content),
        ("Legal monetary total", "<cac:LegalMonetaryTotal>" in content),
        ("Invoice lines", "<cac:InvoiceLine>" in content),
        ("Line quantities", "<cbc:InvoicedQuantity" in content),
        ("Line amounts", "<cbc:LineExtensionAmount" in content),
    ]
    
    passed = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n📊 COMPATIBILITY SCORE: {passed}/{len(checks)} ({passed/len(checks)*100:.0f}%)")
    
    if passed == len(checks):
        print("🎉 All Hostfact compatibility checks passed!")
        return True
    else:
        print("⚠️  Some compatibility issues remain")
        return False

def main():
    """Run all verification checks."""
    print("🏥 Hostfact Compatibility Verification")
    print("=" * 60)
    
    try:
        # Compare files
        compare_result = compare_xml_files()
        
        # Check Hostfact requirements
        hostfact_result = check_hostfact_requirements()
        
        if compare_result and hostfact_result:
            print("\n🎉 SUCCESS: XML should now be compatible with Hostfact!")
            print("\n📝 Next steps:")
            print("   1. Try importing test_hostfact_fixed.xml into Hostfact")
            print("   2. If successful, process your PDF:")
            print("      ./pdf2ubl.py convert your_invoice.pdf")
            print("   3. Import the generated XML into Hostfact")
        else:
            print("\n⚠️  Some issues may remain. Check the output above.")
            
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()