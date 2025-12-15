#!/usr/bin/env python3
"""
Generate static HTML website from action catalog.
Outputs to docs/ directory for GitHub Pages deployment.
"""

import json
from pathlib import Path
from datetime import datetime

CATALOG_DIR = Path.cwd() / "catalog"
DOCS_DIR = Path.cwd() / "docs"

def load_catalog():
    """Load all catalog entries."""
    actions = []

    for entry_dir in sorted(CATALOG_DIR.iterdir()):
        if not entry_dir.is_dir():
            continue

        latest_file = entry_dir / "latest.json"
        if latest_file.exists():
            with open(latest_file, "r") as f:
                action = json.load(f)
            actions.append(action)

    return actions

def get_all_categories(actions):
    """Get unique categories from all actions."""
    categories = set()
    for action in actions:
        for cat in action.get("annotations", {}).get("categories", []):
            categories.add(cat)
    return sorted(list(categories))

def get_action_type(action):
    """Determine if action is marketplace or internal."""
    source = action.get("source", {})

    if source.get("type") == "marketplace":
        return "marketplace"
    elif source.get("type") == "internal":
        return "internal"

    action_id = action.get("action_id", "").lower()
    if action_id.startswith("marketplace/"):
        return "marketplace"

    return "internal"

def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def load_action_yml(action):
    """Load action.yml for an action."""
    action_id = action.get("action_id", "")
    sanitized_id = action_id.replace("/", "__")

    entry_dir = CATALOG_DIR / sanitized_id
    if not entry_dir.exists():
        return None

    action_yml_path = entry_dir / "action.yml"
    if action_yml_path.exists():
        with open(action_yml_path, "r") as f:
            return f.read()

    return None

def generate_action_card(action):
    """Generate HTML card for an action."""
    action_id = action.get("action_id", "")
    sanitized_id = action_id.replace("/", "__")
    name = action.get("definition", {}).get("name", "")
    description = action.get("definition", {}).get("description", "")
    categories = action.get("annotations", {}).get("categories", [])
    verified = action.get("source", {}).get("verified", False)
    publisher = action.get("source", {}).get("publisher", "")
    action_type = get_action_type(action)

    # Truncate description
    if len(description) > 120:
        description = description[:120] + "..."

    # Get primary category
    primary_category = categories[0] if categories else ""
    more_count = len(categories) - 1 if len(categories) > 1 else 0

    primary_badge = f'<span class="badge badge-category-primary">{escape_html(primary_category)}</span>' if primary_category else ""
    more_badge = f'<span class="badge badge-more">+{more_count}</span>' if more_count > 0 else ""

    verified_badge = ""
    if verified:
        verified_badge = '<span class="badge badge-verified">✓ Verified</span>'

    type_badge = f'<span class="badge badge-{action_type}">{action_type.capitalize()}</span>'

    return f'''
    <div class="action-card" data-action="{escape_html(action_id)}" data-categories="{','.join(categories)}">
        <div class="card-header">
            <h3>{escape_html(name or action_id)}</h3>
            {verified_badge}
        </div>
        <p class="card-description">{escape_html(description)}</p>
        <div class="card-meta">
            <small>Publisher: <strong>{escape_html(publisher or "internal")}</strong></small>
        </div>
        <div class="card-badges">
            {type_badge}
            {primary_badge}
            {more_badge}
        </div>
        <a href="#" class="card-link" data-action-id="{escape_html(sanitized_id)}">View Details →</a>
    </div>
'''

def generate_action_modal(action):
    """Generate modal HTML for action details."""
    action_id = action.get("action_id", "")
    sanitized_id = action_id.replace("/", "__")
    definition = action.get("definition", {})
    annotations = action.get("annotations", {})
    source = action.get("source", {})

    name = definition.get("name", "")
    description = definition.get("description", "")
    author = definition.get("author", "")
    inputs = definition.get("inputs", [])
    outputs = definition.get("outputs", [])
    categories = annotations.get("categories", [])
    verified = source.get("verified", False)
    publisher = source.get("publisher", "")
    origin = source.get("origin", "")

    # Load action.yml
    action_yml = load_action_yml(action)

    # Build inputs section
    inputs_html = ""
    if inputs:
        inputs_html = '<div class="section"><h3>Inputs</h3><table class="inputs-table"><thead><tr><th>Name</th><th>Required</th><th>Description</th></tr></thead><tbody>'
        for inp in inputs:
            required = "Yes" if inp.get("required") else "No"
            inputs_html += f'''<tr>
                <td><code>{escape_html(inp.get("name", ""))}</code></td>
                <td>{required}</td>
                <td>{escape_html(inp.get("description", ""))}</td>
            </tr>'''
        inputs_html += '</tbody></table></div>'

    # Build outputs section
    outputs_html = ""
    if outputs:
        outputs_html = '<div class="section"><h3>Outputs</h3><table class="outputs-table"><thead><tr><th>Name</th><th>Description</th></tr></thead><tbody>'
        for out in outputs:
            outputs_html += f'''<tr>
                <td><code>{escape_html(out.get("name", ""))}</code></td>
                <td>{escape_html(out.get("description", ""))}</td>
            </tr>'''
        outputs_html += '</tbody></table></div>'

    # Build categories section - show all categories
    categories_html = ""
    if categories:
        category_badges = ""
        for cat in categories:
            category_badges += f'<span class="badge badge-category-primary">{escape_html(cat)}</span>'
        categories_html = f'<div class="section"><h3>Categories</h3><p>{category_badges}</p></div>'

    # Build action.yml section
    action_yml_html = ""
    if action_yml:
        action_yml_escaped = escape_html(action_yml)
        action_yml_html = f'''<div class="section">
            <h3>action.yml</h3>
            <pre><code>{action_yml_escaped}</code></pre>
        </div>'''

    # Build verification badge
    verified_badge = ""
    if verified:
        verified_badge = '<span class="badge badge-verified">✓ Official Publisher</span>'

    return f'''
    <div id="modal-{escape_html(sanitized_id)}" class="modal" data-action="{escape_html(action_id)}">
        <div class="modal-content">
            <span class="close">&times;</span>

            <h1>{escape_html(name or action_id)}</h1>
            {verified_badge}

            <div class="modal-section">
                <p><strong>Action ID:</strong> <code>{escape_html(action_id)}</code></p>
                <p><strong>Author:</strong> {escape_html(author or "Unknown")}</p>
                {f'<p><strong>Publisher:</strong> {escape_html(publisher)}</p>' if publisher else ''}
                {f'<p><strong>Repository:</strong> <a href="https://{escape_html(origin)}" target="_blank">{escape_html(origin)}</a></p>' if origin else ''}
            </div>

            <div class="modal-section">
                <h2>Description</h2>
                <p>{escape_html(description)}</p>
            </div>

            {categories_html}
            {inputs_html}
            {outputs_html}
            {action_yml_html}
        </div>
    </div>
'''

def generate_index():
    """Generate main index page."""
    actions = load_catalog()
    categories = get_all_categories(actions)

    # Generate action cards
    cards_html = ""
    for action in actions:
        cards_html += generate_action_card(action)

    # Generate modals
    modals_html = ""
    for action in actions:
        modals_html += generate_action_modal(action)

    # Generate category filters
    category_options = ""
    for cat in categories:
        category_options += f'<option value="{escape_html(cat)}">{escape_html(cat)}</option>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Actions Catalog</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="index.html" class="navbar-brand">🚀 Actions Catalog</a>
            <p class="navbar-subtitle">Browse {len(actions)} GitHub Actions</p>
        </div>
    </nav>

    <main class="container">
        <div class="search-section">
            <input type="text" id="searchInput" class="search-input" placeholder="Search actions by name or description...">

            <div class="filter-group">
                <select id="categoryFilter" class="category-filter">
                    <option value="">All Categories</option>
                    {category_options}
                </select>

                <select id="typeFilter" class="category-filter">
                    <option value="">All Types</option>
                    <option value="internal">Internal Only</option>
                    <option value="marketplace">Marketplace Only</option>
                </select>
            </div>
        </div>

        <div class="results-info">
            <p id="resultCount">Showing {len(actions)} actions</p>
        </div>

        <div class="actions-grid">
            {cards_html}
        </div>
    </main>

    {modals_html}

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
    </footer>

    <script>
        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const typeFilter = document.getElementById('typeFilter');
        const cards = document.querySelectorAll('.action-card');
        const resultCount = document.getElementById('resultCount');
        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.close');

        // Open modal when card is clicked
        cards.forEach(card => {{
            card.addEventListener('click', (e) => {{
                if (e.target.closest('.card-link')) {{
                    e.preventDefault();
                }}
                const actionId = card.querySelector('.card-link').getAttribute('data-action-id');
                const modal = document.getElementById(`modal-${{actionId}}`);
                if (modal) {{
                    modal.style.display = 'block';
                }}
            }});
        }});

        // Close modal
        closeButtons.forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                const modal = e.target.closest('.modal');
                if (modal) {{
                    modal.style.display = 'none';
                }}
            }});
        }});

        // Close modal when clicking outside
        modals.forEach(modal => {{
            modal.addEventListener('click', (e) => {{
                if (e.target === modal) {{
                    modal.style.display = 'none';
                }}
            }});
        }});

        function filterActions() {{
            const searchTerm = searchInput.value.toLowerCase();
            const selectedCategory = categoryFilter.value;
            const selectedType = typeFilter.value;
            let visibleCount = 0;

            cards.forEach(card => {{
                const action = card.getAttribute('data-action').toLowerCase();
                const categories = card.getAttribute('data-categories').split(',').filter(c => c);
                const name = card.querySelector('h3').textContent.toLowerCase();
                const description = card.querySelector('.card-description').textContent.toLowerCase();
                const typeElement = card.querySelector('.badge');
                const actionType = typeElement.textContent.toLowerCase();

                const matchesSearch = !searchTerm ||
                    action.includes(searchTerm) ||
                    name.includes(searchTerm) ||
                    description.includes(searchTerm);

                const matchesCategory = !selectedCategory || categories.includes(selectedCategory);

                const matchesType = !selectedType || actionType.includes(selectedType);

                if (matchesSearch && matchesCategory && matchesType) {{
                    card.style.display = 'block';
                    visibleCount++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            resultCount.textContent = `Showing ${{visibleCount}} action${{visibleCount !== 1 ? 's' : ''}}`;
        }}

        searchInput.addEventListener('input', filterActions);
        categoryFilter.addEventListener('change', filterActions);
        typeFilter.addEventListener('change', filterActions);
    </script>
</body>
</html>'''

def generate_styles():
    """Generate CSS stylesheet."""
    return '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary: #0969da;
    --primary-dark: #0860ca;
    --success: #1a7f37;
    --gray-100: #f6f8fa;
    --gray-200: #eaeef2;
    --gray-300: #d0d7de;
    --gray-600: #57606a;
    --gray-700: #424a53;
    --gray-800: #2d333b;
    --gray-900: #0d1117;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--gray-800);
    background: var(--gray-100);
}

.navbar {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    padding: 2rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: 600;
    text-decoration: none;
    color: white;
}

.navbar-subtitle {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

.search-section {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.search-input {
    flex: 1;
    min-width: 250px;
    padding: 0.75rem 1rem;
    border: 1px solid var(--gray-300);
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.search-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
}

.filter-group {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.category-filter {
    padding: 0.75rem 1rem;
    border: 1px solid var(--gray-300);
    border-radius: 6px;
    font-size: 1rem;
    background: white;
    cursor: pointer;
    transition: border-color 0.2s;
}

.category-filter:focus {
    outline: none;
    border-color: var(--primary);
}

.results-info {
    margin-bottom: 1.5rem;
    color: var(--gray-600);
}

.actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.action-card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.2s;
    cursor: pointer;
    display: flex;
    flex-direction: column;
}

.action-card:hover {
    border-color: var(--primary);
    box-shadow: 0 3px 12px rgba(9, 105, 218, 0.15);
    transform: translateY(-2px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}

.card-header h3 {
    font-size: 1.1rem;
    margin: 0;
    flex: 1;
    word-break: break-word;
}

.card-description {
    color: var(--gray-600);
    margin-bottom: 1rem;
    flex-grow: 1;
}

.card-meta {
    margin-bottom: 1rem;
    color: var(--gray-600);
    font-size: 0.9rem;
}

.card-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.card-link {
    color: var(--primary);
    font-weight: 500;
    margin-top: auto;
    text-decoration: none;
}

.card-link:hover {
    text-decoration: underline;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
    white-space: nowrap;
}

.badge-category-primary {
    background: #3b2667;
    color: white;
    font-weight: 600;
}

.badge-verified {
    background: var(--success);
    color: white;
}

.badge-internal {
    background: #3b2667;
    color: white;
}

.badge-marketplace {
    background: var(--primary);
    color: white;
}

.badge-more {
    background: var(--gray-300);
    color: var(--gray-800);
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.4);
    overflow-y: auto;
}

.modal-content {
    background: white;
    margin: 2rem auto;
    padding: 2rem;
    border-radius: 8px;
    max-width: 900px;
    max-height: 90vh;
    overflow-y: auto;
    border: 1px solid var(--gray-300);
}

.close {
    color: var(--gray-600);
    float: right;
    font-size: 2rem;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: var(--gray-900);
}

.modal-content h1 {
    margin: 0 0 1rem 0;
    font-size: 1.8rem;
}

.modal-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.modal-section:last-child {
    border-bottom: none;
}

.modal-section h2,
.modal-section h3 {
    margin: 0 0 1rem 0;
}

.section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.section:last-child {
    border-bottom: none;
}

.section h3 {
    margin: 0 0 1rem 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--gray-200);
}

th {
    background: var(--gray-100);
    font-weight: 600;
}

code {
    background: var(--gray-100);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
}

pre {
    background: var(--gray-900);
    color: #f0f0f0;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin-top: 1rem;
}

pre code {
    background: none;
    padding: 0;
    color: inherit;
    font-size: 0.9rem;
}

footer {
    background: var(--gray-900);
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
}

@media (max-width: 768px) {
    .actions-grid {
        grid-template-columns: 1fr;
    }

    .search-section {
        flex-direction: column;
    }

    .search-input {
        min-width: auto;
    }

    .filter-group {
        flex-direction: column;
    }

    .modal-content {
        margin: 1rem;
        padding: 1rem;
    }
}
'''

def main():
    """Generate website."""
    print("🌐 Generating static website for GitHub Pages\n")

    # Create docs directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Load catalog
    actions = load_catalog()
    print(f"📚 Loaded {len(actions)} actions\n")

    # Generate index.html
    print("📄 Generating index.html...")
    index_html = generate_index()
    with open(DOCS_DIR / "index.html", "w") as f:
        f.write(index_html)
    print("   ✅ index.html")

    # Generate styles.css
    print("📄 Generating styles.css...")
    styles = generate_styles()
    with open(DOCS_DIR / "styles.css", "w") as f:
        f.write(styles)
    print("   ✅ styles.css")

    print(f"\n✅ Website generated successfully!")
    print(f"📁 Output: {DOCS_DIR.relative_to(Path.cwd())}/")
    print(f"🚀 Ready for GitHub Pages deployment")

if __name__ == "__main__":
    main()
