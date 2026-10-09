#!/usr/bin/env python3
"""
Extract district-wise water quality data from CGWB Ground Water Year Book PDFs.

CGWB Year Books contain district-level tables for:
- pH, EC (Electrical Conductivity), Fluoride, Arsenic, Iron, Nitrate, TDS, Sulphate
- Covers ALL districts in UP (75) + Bihar (38)

Usage:
    python extract_cgwb.py --state up --download
    python extract_cgwb.py --state bihar --download
    python extract_cgwb.py --state both --download
    python extract_cgwb.py --state both --input-dir ./cgwb_pdfs --output-csv cgwb_data.csv
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import pdfplumber
import requests
from tqdm import tqdm


# Known CGWB Year Book URLs (update as needed)
CGWB_URLS = {
    "up": [
        "https://cgwb.gov.in/GW-Year-Book/GWYB-UP-2022-23.pdf",
        "https://cgwb.gov.in/GW-Year-Book/GWYB-UP-2021-22.pdf",
        "https://cgwb.gov.in/GW-Year-Book/GWYB-UP-2020-21.pdf",
    ],
    "bihar": [
        "https://cgwb.gov.in/GW-Year-Book/GWYB-BR-2022-23.pdf",
        "https://cgwb.gov.in/GW-Year-Book/GWYB-BR-2021-22.pdf",
        "https://cgwb.gov.in/GW-Year-Book/GWYB-BR-2020-21.pdf",
    ],
}

# Parameter name mapping to standardize
PARAM_MAP = {
    "ph": "ph",
    "pH": "ph",
    "ec": "ec",
    "electrical conductivity": "ec",
    "fluoride": "fluoride",
    "f": "fluoride",
    "arsenic": "arsenic",
    "as": "arsenic",
    "iron": "iron",
    "fe": "iron",
    "nitrate": "nitrate",
    "no3": "nitrate",
    "tds": "tds",
    "total dissolved solids": "tds",
    "sulphate": "sulphate",
    "sulfate": "sulphate",
    "so4": "sulphate",
    "chloride": "chloride",
    "cl": "chloride",
    "hardness": "hardness",
    "calcium": "calcium",
    "magnesium": "magnesium",
    "sodium": "sodium",
    "potassium": "potassium",
    "bicarbonate": "bicarbonate",
    "hco3": "bicarbonate",
    "carbonate": "carbonate",
    "co3": "carbonate",
}

# Known UP districts (75)
UP_DISTRICTS = {
    "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya",
    "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki",
    "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli",
    "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad",
    "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur",
    "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat",
    "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur",
    "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur",
    "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli",
    "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli",
    "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
}

# Known Bihar districts (38)
BIHAR_DISTRICTS = {
    "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur",
    "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad",
    "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani",
    "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa",
    "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul",
    "Vaishali", "West Champaran"
}

ALL_DISTRICTS = UP_DISTRICTS | BIHAR_DISTRICTS


def normalize_district(name: str) -> Optional[str]:
    """Normalize district name to match our known list."""
    name = name.strip()
    # Try exact match
    for d in ALL_DISTRICTS:
        if d.lower() == name.lower():
            return d
    # Try partial match
    for d in ALL_DISTRICTS:
        if d.lower() in name.lower() or name.lower() in d.lower():
            return d
    return None


def normalize_param(name: str) -> Optional[str]:
    """Normalize parameter name."""
    name = name.strip().lower()
    for k, v in PARAM_MAP.items():
        if k.lower() == name or k.lower() in name:
            return v
    return None


def download_pdf(url: str, output_path: Path) -> bool:
    """Download a PDF file."""
    try:
        headers = {"User-Agent": "WaterTriage-ETL/0.1 (academic research)"}
        resp = requests.get(url, headers=headers, timeout=120, stream=True, verify=False)
        resp.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


def extract_tables_from_pdf(pdf_path: Path, state: str, year: str) -> list[dict]:
    """Extract water quality tables from CGWB PDF."""
    records = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Try to identify header row
                    header_row = None
                    header_idx = -1
                    for i, row in enumerate(table):
                        if row and any(cell and "district" in str(cell).lower() for cell in row):
                            header_row = row
                            header_idx = i
                            break
                    
                    if header_row is None:
                        # Try to find parameter header
                        for i, row in enumerate(table):
                            if row and any(cell and any(p in str(cell).lower() for p in PARAM_MAP) for cell in row):
                                header_row = row
                                header_idx = i
                                break
                    
                    if header_row is None:
                        continue
                    
                    # Find column indices
                    district_col = None
                    param_cols = {}  # param_name -> col_idx
                    
                    for j, cell in enumerate(header_row):
                        if not cell:
                            continue
                        cell_lower = str(cell).lower()
                        if "district" in cell_lower:
                            district_col = j
                        else:
                            param = normalize_param(str(cell))
                            if param:
                                param_cols[j] = param
                    
                    if district_col is None or not param_cols:
                        continue
                    
                    # Process data rows
                    for row in table[header_idx + 1:]:
                        if not row or len(row) <= district_col:
                            continue
                        
                        district_raw = row[district_col]
                        if not district_raw:
                            continue
                        
                        district = normalize_district(str(district_raw))
                        if not district:
                            continue
                        
                        for col_idx, param in param_cols.items():
                            if col_idx >= len(row):
                                continue
                            value_raw = row[col_idx]
                            if not value_raw:
                                continue
                            # Try to extract numeric value
                            val_str = str(value_raw).strip()
                            # Handle ranges like "0.5-1.2" or "BDL"
                            if val_str.upper() in ("BDL", "ND", "NIL", "-", "NA"):
                                continue
                            # Extract first number
                            num_match = re.search(r"[\d.]+", val_str.replace(",", ""))
                            if not num_match:
                                continue
                            try:
                                value = float(num_match.group())
                                records.append({
                                    "state": state,
                                    "district": district,
                                    "parameter": param,
                                    "value": value,
                                    "year": year,
                                    "source": "CGWB Year Book",
                                    "pdf_page": page_num + 1,
                                })
                            except ValueError:
                                continue
    except Exception as e:
        print(f"Error extracting from {pdf_path}: {e}")
    
    return records


def extract_year_from_filename(filename: str) -> str:
    """Extract year from filename like GWYB-UP-2022-23.pdf"""
    match = re.search(r"(\d{4})-(\d{2})", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"(\d{4})", filename)
    if match:
        return match.group(1)
    return "unknown"


def main():
    ap = argparse.ArgumentParser(description="Extract CGWB Year Book water quality data")
    ap.add_argument("--state", choices=["up", "bihar", "both"], default="both")
    ap.add_argument("--download", action="store_true", help="Download PDFs before extracting")
    ap.add_argument("--input-dir", default="./data/cgwb_pdfs", help="Directory with PDF files")
    ap.add_argument("--output-csv", default="./data/cgwb_extracted.csv", help="Output CSV path")
    ap.add_argument("--max-pages", type=int, default=0, help="Max pages per PDF (0 = all)")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    input_dir.mkdir(parents=True, exist_ok=True)

    states = ["up", "bihar"] if args.state == "both" else [args.state]
    all_records = []

    for state in states:
        print(f"\n=== Processing {state.upper()} ===")
        
        # Download if requested
        if args.download:
            for url in CGWB_URLS[state]:
                filename = url.split("/")[-1]
                pdf_path = input_dir / filename
                if not pdf_path.exists():
                    download_pdf(url, pdf_path)
                else:
                    print(f"Already exists: {pdf_path}")
        
        # Find PDF files
        pdf_files = list(input_dir.glob(f"*{state.upper()}*.pdf")) + list(input_dir.glob(f"*-{state[0].upper()}*.pdf"))
        if not pdf_files:
            pdf_files = list(input_dir.glob("*.pdf"))
        
        pdf_files = [f for f in pdf_files if state[0].upper() in f.name.upper() or state.upper() in f.name.upper()]
        
        if not pdf_files:
            print(f"No PDF files found for {state} in {input_dir}")
            continue
        
        for pdf_path in pdf_files:
            print(f"Extracting from {pdf_path.name}...")
            year = extract_year_from_filename(pdf_path.name)
            records = extract_tables_from_pdf(pdf_path, state, year)
            print(f"  Extracted {len(records)} records")
            all_records.extend(records)

    # Write CSV
    if all_records:
        import csv
        output_path = Path(args.output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ["state", "district", "parameter", "value", "year", "source", "pdf_page"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"\n✅ Written {len(all_records)} records to {output_path}")
        
        # Summary by district
        districts_found = set(r["district"] for r in all_records)
        print(f"Districts covered: {len(districts_found)} / {len(ALL_DISTRICTS)}")
        print(f"Districts: {', '.join(sorted(districts_found))}")
        
        # Summary by parameter
        params = {}
        for r in all_records:
            params[r["parameter"]] = params.get(r["parameter"], 0) + 1
        print("Parameters:")
        for p, c in sorted(params.items(), key=lambda x: -x[1]):
            print(f"  {p}: {c}")
    else:
        print("\n❌ No records extracted")


if __name__ == "__main__":
    main()