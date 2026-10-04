import glob
from bs4 import BeautifulSoup
import re
import hashlib
import shutil
import os

files = glob.glob('/home/anubhavanand/Downloads/Format WQ6*.xls')
files.sort()

os.makedirs('data/raw/official', exist_ok=True)

for fpath in files:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    state_span = soup.find('span', class_='State_Name')
    state = state_span.get_text(strip=True).title() if state_span else "Unknown"
            
    districts = set()
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 18:
            d = cells[1].get_text(strip=True)
            if d and not d.isdigit() and d not in ['Total', 'S.No.', 'District name', 'State']:
                districts.add(re.sub(r'\(\d+\)', '', d).strip().title())
    
    filename = fpath.split('/')[-1]
    print(f"--- FILE: {filename} ---")
    print(f">> State parsed: {state}")
    print(f">> Distinct districts: {len(districts)}")
    
    if state in ['Bihar', 'Uttar Pradesh']:
        h = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
        new_name = f"data/raw/official/WQ6_{state.replace(' ', '')}_{h}.xls"
        shutil.copy(fpath, new_name)
        print(f">> Copied to {new_name}")
    print("--------------------------------------------------")

