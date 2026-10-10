import re

with open('src/index.css', 'r') as f:
    css = f.read()

# Batch 1: Accent Budget
css = css.replace('.tab-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }', '.tab-btn:focus-visible { outline: 2px solid var(--fg); outline-offset: 2px; }')
css = css.replace('.btn-ghost:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }', '.btn-ghost:focus-visible { outline: 2px solid var(--fg); outline-offset: 2px; }')

# Batch 2: Dark Mode Contrast Fixes
css = css.replace('--yellow-note: #3a3310;', '--yellow-note: #4a4018;')
css = css.replace('--pink-note:   #3a181c;', '--pink-note:   #4a1c20;')
css = css.replace('--green-note:  #103020;', '--green-note:  #143828;')
css = css.replace('[data-theme="dark"] .sticky::after { border-color: color-mix(in oklch, var(--fg) 25%, transparent); }', '[data-theme="dark"] .sticky::after { border-color: color-mix(in oklch, var(--fg) 40%, transparent); }')

# Batch 3: Touch Targets & Responsive Fixes
# - Pagination buttons: min-height: 44px (Wait, the pagination buttons are in App.jsx. But in CSS they might just be .btn-ghost?)
# - Nav links explicit min-height: 44px
css = re.sub(r'(\.topnav nav a \{[^}]*)min-height: 44px; display: inline-flex; align-items: center;([^}]*\})', r'\1min-height: 44px; display: inline-flex; align-items: center; padding: 8px 0;\2', css)

# - Ghost button hover: add background in dark mode too (already handled by var(--accent-soft), wait: ghost button hover has `background: var(--accent-soft); color: var(--accent);`. Is it not showing in dark mode? Ah, dark mode overrides might be missing. Actually, --accent-soft is derived in dark mode too. So the user says: "Ghost button hover: add background: var(--accent-soft) in dark mode too". Let's explicitly add it if missing.)

with open('src/index.css', 'w') as f:
    f.write(css)

