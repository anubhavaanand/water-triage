import re

with open('src/App.jsx', 'r') as f:
    jsx = f.read()

# Replace Tab C (Unnao selected row border) to fg
# <div style={{padding: '11px 14px', borderBottom: '1px dashed var(--border)', background: 'var(--accent-soft)', borderLeft: '3px solid var(--accent)', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--fg)', display: 'flex', justifyContent: 'space-between'}}><span>Unnao, UP ← selected</span>
jsx = jsx.replace(
    "background: 'var(--accent-soft)', borderLeft: '3px solid var(--accent)'",
    "background: 'var(--fg-soft)', borderLeft: '3px solid var(--fg)'"
)

# Tab B "Selected pill" is fine according to budget. 
# Tab B Map View placeholder border -> --fg? (Wait, Map View placeholder is line 895, it's not Tab B, it's the User Flow diagram.)
# Let's replace the flow diagram map view with fg
jsx = jsx.replace(
    "border: '2px solid var(--accent)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--accent-soft)', color: 'var(--accent)'",
    "border: '2px solid var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--surface)', color: 'var(--fg)'"
)

# Tab C prog-fill -> let's keep it (it's allowed per budget)
# Charts donut segment -> allowed
# Are there any empty/error states with --accent?
# Line 218/219 Unnao selected card
jsx = jsx.replace(
    "border: '2px solid var(--accent)', borderTop: 'none', background: 'var(--accent-soft)'",
    "border: '2px solid var(--fg)', borderTop: 'none', background: 'var(--fg-soft)'"
)
jsx = jsx.replace(
    "color: 'var(--accent)'}}>Unnao, UP",
    "color: 'var(--fg)'}}>Unnao, UP"
)

with open('src/App.jsx', 'w') as f:
    f.write(jsx)

