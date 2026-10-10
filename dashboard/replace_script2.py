import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Replace Hero text
content = re.sub(
    r"Data: <strong>1,741 samples</strong> across <strong>47 districts</strong> \(UP 28 / Bihar 19\)\.",
    r"Data: <strong>{metaData?.corpus?.samples ?? '1,741'} samples</strong> across <strong>{metaData?.corpus?.districts_with_samples ?? '49'} districts</strong>.",
    content
)

# Replace Validation point VP-1 text
content = re.sub(
    r"<span className=\"num\">70</span>",
    r"<span className=\"num\">{metaData?.critical_concentration?.total_critical ?? 70}</span>",
    content
)

with open('src/App.jsx', 'w') as f:
    f.write(content)
