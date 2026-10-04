import re

with open('src/lib/components/QueueTab.svelte', 'r') as f:
    content = f.read()

# Fix priority list extraction
content = re.sub(
    r"priorityList = data\.priority \|\| \[\];",
    r"priorityList = Array.isArray(data) ? data : (data.priority || []);",
    content
)

# Insert Drawer import and state
import_code = """
  import { onMount } from 'svelte';
  import Drawer from './Drawer.svelte';
  
  let selectedSampleId = $state(null);
"""
content = re.sub(r"import \{ onMount \} from 'svelte';", import_code, content)

# Make the row clickable
content = content.replace(
    '<div aria-label={isPathogen ? "Pathogen override row" : ""} style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px;',
    '<div class="queue-item" onclick={() => selectedSampleId = item.sample_id} role="button" tabindex="0" onkeydown={(e) => e.key === \'Enter\' && (selectedSampleId = item.sample_id)} aria-label={isPathogen ? "Pathogen override row" : ""} style="cursor:pointer; display: grid; grid-template-columns: 1fr 80px 90px 80px 80px;'
)

# Append the Drawer element at the end
drawer_code = """
{#if selectedSampleId}
  <Drawer sampleId={selectedSampleId} onClose={() => selectedSampleId = null} />
{/if}
</div>
"""
content = content.replace('</div>\n</div>\n</div>', '</div>\n' + drawer_code + '\n</div>')

with open('src/lib/components/QueueTab.svelte', 'w') as f:
    f.write(content)

