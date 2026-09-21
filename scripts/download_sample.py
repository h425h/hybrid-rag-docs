import httpx
from pathlib import Path

# APRA CPS 234: Information Security
PDF_URL = "https://www.apra.gov.au/sites/default/files/CPS-234-July-2019.pdf"
DEST_DIR = Path("data/raw")
DEST_FILE = DEST_DIR / "CPS_234_Information_Security.pdf"


def download_benchmark_doc():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if DEST_FILE.exists() and DEST_FILE.stat().st_size > 1000:
        print(f"File already exists and valid at {DEST_FILE}")
        return

    print(f"Downloading APRA CPS 234 from {PDF_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(PDF_URL, headers=headers)
        response.raise_for_status()
        DEST_FILE.write_bytes(response.content)
    print(f"Successfully saved to {DEST_FILE} ({len(response.content) // 1024} KB)")


if __name__ == "__main__":
    download_benchmark_doc()