import re

with open('src/index.css', 'r') as f:
    css = f.read()

# Make the tab panel note responsive
css = re.sub(
    r'@media \(max-width: 1300px\) \{ \.tab-panel::before \{ display: none; \} \}',
    """
    @media (max-width: 1300px) {
      .tab-panel::before {
        position: static;
        display: block;
        width: auto;
        margin-top: var(--gap-lg);
        padding-top: 12px;
        padding-left: 0;
        border-left: none;
        border-top: 1px dashed var(--border);
      }
    }
    """, css
)

with open('src/index.css', 'w') as f:
    f.write(css)

