with open('Overview.svelte', 'r') as f:
    content = f.read()

old_caption = "70 of 89 Critical samples are single-parameter iron results from one district"
new_caption = "{meta.critical_concentration.single_parameter_iron_critical} of {meta.critical_concentration.total_critical} Critical samples are single-parameter iron results from {meta.critical_concentration.district} district"

content = content.replace(old_caption, new_caption)

# Replace fetch URL to relative
content = content.replace("'http://localhost:8000/api/meta'", "'/api/meta'")

with open('Overview.svelte', 'w') as f:
    f.write(content)

with open('Methodology.svelte', 'r') as f:
    m_content = f.read()
    m_content = m_content.replace("'http://localhost:8000/api/meta'", "'/api/meta'")
with open('Methodology.svelte', 'w') as f:
    f.write(m_content)
