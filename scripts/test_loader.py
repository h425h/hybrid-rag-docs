import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.loader import LayoutAwareLoader

# Point directly to our newly downloaded ASIC regulatory guide
PDF_PATH = "data/raw/ASIC_RG274.pdf"

loader = LayoutAwareLoader()
result = loader.load_pdf(PDF_PATH)

print("\n================ PARSE AUDIT ================")
print(f"Document ID:      {result.document_id}")
print(f"File Name:        {result.file_name}")
print(f"Parse Confidence: {result.confidence.value}")
print(f"Total Elements:   {result.total_elements}")
print(f"Tables Detected:  {result.total_tables}")
print(f"Validation Flags: {result.flags[:5]}")

print("\n================ ELEMENT PREVIEW (FIRST 5) ================")
for idx, elem in enumerate(result.elements[:5]):
    print(f"\n[{idx+1}] Type: {elem.element_type.value} | Page: {elem.metadata.get('page')}")
    print(f"Content:\n{elem.text[:140]}...")

if result.total_tables > 0:
    print("\n================ FIRST TABLE DETECTED ================")
    table_elem = next(e for e in result.elements if e.element_type.value == "Table")
    print(f"Headers: {table_elem.table_data.headers}")
    print(f"Row count: {table_elem.table_data.row_count}")
    print("Content preview:")
    print(table_elem.text[:250])