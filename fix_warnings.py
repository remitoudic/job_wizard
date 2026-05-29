import os
import re

files_to_clean = [
    "/root/job_wizard/services/frontend/src/routes/+page.svelte",
    "/root/job_wizard/services/frontend/src/routes/+layout.svelte",
    "/root/job_wizard/services/frontend/src/routes/admin/+page.svelte",
    "/root/job_wizard/services/frontend/src/routes/profile/+page.svelte",
]

for file_path in files_to_clean:
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r") as f:
        content = f.read()

    # Remove unused data and params exports
    content = re.sub(r"^\s*//\s*SvelteKit.*?\n", "", content, flags=re.MULTILINE)
    content = re.sub(
        r"^\s*export let data(?::\s*any)?(\s*=\s*\{\})?;\s*\n?",
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^\s*export let params(?::\s*Record<string,\s*string>)?(\s*=\s*\{\})?;\s*\n?",
        "",
        content,
        flags=re.MULTILINE,
    )

    with open(file_path, "w") as f:
        f.write(content)

# Fix a11y in applications/+page.svelte
app_page = "/root/job_wizard/services/frontend/src/routes/applications/+page.svelte"
with open(app_page, "r") as f:
    content = f.read()

# Replace <div ... on:click={() => handleSort('company')}>
content = content.replace(
    """<div
										class="flex items-center gap-1 cursor-pointer hover:text-[#0369A1] transition-colors"
										on:click={() => handleSort('company')}
									>""",
    """<button
										type="button"
										class="flex items-center gap-1 cursor-pointer hover:text-[#0369A1] transition-colors"
										on:click={() => handleSort('company')}
									>""",
)
# We also need to change the closing tag for this div to </button>
# It's at line 506. Let's just use regex for this specific block:
content = re.sub(
    r'(<div\s+class="flex items-center gap-1 cursor-pointer hover:text-\[#0369A1\] transition-colors"\s+on:click=\{\(\) => handleSort\(\'company\'\)\}\s*>)(.*?)(</div>)',
    r'<button type="button" class="flex items-center gap-1 cursor-pointer hover:text-[#0369A1] transition-colors" on:click={() => handleSort(\'company\')}>\2</button>',
    content,
    flags=re.DOTALL,
)

# Fix click outside
content = re.sub(
    r'(<div\s+class="fixed inset-0 z-10"\s+on:click=\{\(\) => \(isFilterVisible = false\)\}\s*>)</div>',
    r'<button type="button" class="fixed inset-0 z-10 cursor-default" on:click={() => (isFilterVisible = false)} aria-label="Close"></button>',
    content,
)

# Fix autofocus
content = content.replace(
    "bind:value={companySearchText}\n\t\t\t\t\t\t\t\t\t\t\t\tautofocus",
    "bind:value={companySearchText}",
)
content = content.replace(
    "bind:value={companySearchText}\n\t\t\t\t\t\t\t\t\t\t\tautofocus",
    "bind:value={companySearchText}",
)

# Fix filter companies div
content = re.sub(
    r'<div\s+class="absolute right-0 mt-2 w-64 bg-white border border-\[#E2E8F0\] rounded-lg shadow-xl p-3 z-20"\s+on:click\|stopPropagation\s*>',
    r'<div role="dialog" class="absolute right-0 mt-2 w-64 bg-white border border-[#E2E8F0] rounded-lg shadow-xl p-3 z-20" on:click|stopPropagation on:keydown|stopPropagation>',
    content,
)

# Fix select div wrapper
content = content.replace(
    '<div class="relative group" on:click|stopPropagation>',
    '<div role="button" tabindex="0" class="relative group" on:click|stopPropagation on:keydown|stopPropagation>',
)

with open(app_page, "w") as f:
    f.write(content)

print("Fixed!")
