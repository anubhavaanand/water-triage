import re

with open("docs/REVIEW_PACKET.md", "r") as f:
    content = f.read()

import subprocess
out = subprocess.run("pdftotext '/home/anubhavanand/Desktop/WaterTriage_Deliverables_05-10-2026/WPR_11_Anubhav_Anand.pdf' - | head -n 30", shell=True, text=True, capture_output=True).stdout

replacement = "Found at `/home/anubhavanand/Desktop/WaterTriage_Deliverables_05-10-2026/WPR_11_Anubhav_Anand.pdf` (saved by user).\n" + out

content = re.sub(r"Not found on disk \(wiped by git clean or workspace reset\)\.", replacement, content)

with open("docs/REVIEW_PACKET.md", "w") as f:
    f.write(content)
