import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
r = requests.get('https://ejalshakti.gov.in/WQMIS/Report/Report_p', verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
scripts = soup.find_all('script')
for s in scripts:
    if s.string and 'Load_ParameterRpt' in s.string:
        print(s.string)
