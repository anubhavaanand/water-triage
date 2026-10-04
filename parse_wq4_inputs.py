import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
r = requests.get('https://ejalshakti.gov.in/WQMIS/Report/Report_p', verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
for select in soup.find_all('select'):
    print("Dropdown:", select.get('name'), select.get('id'))
for input in soup.find_all('input', type=lambda t: t != 'hidden'):
    print("Input:", input.get('name'), input.get('id'), input.get('type'))
