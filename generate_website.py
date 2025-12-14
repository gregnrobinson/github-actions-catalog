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

def generate_action_card(action):
    """Generate HTML card for an action."""
    action_id = action.get("action_id", "")
    sanitized_id = action_id.replace("/", "__")
    name = action.get("definition", {}).get("name", "")
    description = action.get("definition", {}).get("description", "")
    categories = action.get("annotations", {}).get("categories", [])
    verified = action.get("source", {}).get("verified", False)
    publisher = action.get("source", {}).get("publisher", "")

    # Truncate description
    if len(description) > 120:
        description = description[:120] + "..."

    category_badges = ""
    for cat in categories[:2]:
        category_badges += f'<span class="badge badge-category">{escape_html(cat)}</span>'

    if len(categories) > 2:
        category_badges += f'<span class="badge badge-more">+{len(categories)-2}</span>'

    verified_badge = ""
    if verified:
        verified_badge = '<span class="badge badge-verified">✓ Verified</span>'

    return f'''
    <a href="{escape_html(sanitized_id)}.html" class="action-card-link">
        <div class="action-card" data-action="{escape_html(action_id)}" data-categories="{','.join(categories)}">
            <div class="card-header">
                <div class="card-title-section">
                    <h3>{escape_html(name or action_id)}</h3>
                </div>
                {verified_badge}
            </div>
            <p class="card-description">{escape_html(description)}</p>
            <div class="card-meta">
                <small>Publisher: <strong>{escape_html(publisher or "internal")}</strong></small>
            </div>
            <div class="card-categories">
                {category_badges}
            </div>
            <div class="card-link">View Details →</div>
        </div>
    </a>
'''

def generate_action_detail(action):
    """Generate HTML detail page for an action."""
    action_id = action.get("action_id", "")
    definition = action.get("definition", {})
    annotations = action.get("annotations", {})
    source = action.get("source", {})
    evidence = annotations.get("evidence", [])

    name = definition.get("name", "")
    description = definition.get("description", "")
    author = definition.get("author", "")
    inputs = definition.get("inputs", [])
    outputs = definition.get("outputs", [])
    categories = annotations.get("categories", [])
    confidence = annotations.get("confidence", "")
    verified = source.get("verified", False)
    publisher = source.get("publisher", "")
    origin = source.get("origin", "")

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

    # Build categories section
    categories_html = ""
    if categories:
        category_badges = " ".join([f'<span class="badge badge-category">{escape_html(cat)}</span>' for cat in categories])
        categories_html = f'<div class="section"><h3>Categories</h3><p>{category_badges}</p></div>'

    # Build evidence section
    evidence_html = ""
    if evidence:
        primary_cat = evidence[0].get("primary_category", "")
        reasoning = evidence[0].get("reasoning", "")
        tags = evidence[0].get("tags", [])

        tags_html = " ".join([f'<span class="tag">{escape_html(tag)}</span>' for tag in tags])

        evidence_html = f'''<div class="section">
            <h3>Categorization</h3>
            <p><strong>Primary:</strong> {escape_html(primary_cat)}</p>
            <p><strong>Confidence:</strong> {escape_html(confidence)}</p>
            <p><strong>Reasoning:</strong> {escape_html(reasoning)}</p>
            {f'<p><strong>Tags:</strong> {tags_html}</p>' if tags else ''}
        </div>'''

    # Build verification badge
    verified_badge = ""
    if verified:
        verified_badge = '<span class="badge badge-verified">✓ Official Publisher</span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(name or action_id)} - Actions Catalog</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="index.html" class="navbar-brand">🚀 Actions Catalog</a>
        </div>
    </nav>

    <main class="container">
        <a href="index.html" class="back-link">← Back to Catalog</a>

        <div class="detail-header">
            <h1>{escape_html(name or action_id)}</h1>
            {verified_badge}
        </div>

        <div class="detail-meta">
            <p><strong>Action ID:</strong> <code>{escape_html(action_id)}</code></p>
            <p><strong>Author:</strong> {escape_html(author or "Unknown")}</p>
            {f'<p><strong>Publisher:</strong> {escape_html(publisher)}</p>' if publisher else ''}
            {f'<p><strong>Repository:</strong> <a href="https://{escape_html(origin)}" target="_blank">{escape_html(origin)}</a></p>' if origin else ''}
        </div>

        <div class="section">
            <h2>Description</h2>
            <p>{escape_html(description)}</p>
        </div>

        {categories_html}
        {evidence_html}
        {inputs_html}
        {outputs_html}
    </main>

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
    </footer>
</body>
</html>'''

def generate_index():
    """Generate main index page."""
    actions = load_catalog()
    categories = get_all_categories(actions)

    # Generate action cards
    cards_html = ""
    for action in actions:
        cards_html += generate_action_card(action)

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

            <select id="categoryFilter" class="category-filter">
                <option value="">All Categories</option>
                {category_options}
            </select>
        </div>

        <div class="results-info">
            <p id="resultCount">Showing {len(actions)} actions</p>
        </div>

        <div class="actions-grid">
            {cards_html}
        </div>
    </main>

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")} | <a href="https://github.com">GitHub Actions Catalog</a></p>
    </footer>

    <script>
        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const cards = document.querySelectorAll('.action-card');
        const resultCount = document.getElementById('resultCount');

        function filterActions() {{
            const searchTerm = searchInput.value.toLowerCase();
            const selectedCategory = categoryFilter.value;
            let visibleCount = 0;

            cards.forEach(card => {{
                const action = card.getAttribute('data-action').toLowerCase();
                const categories = card.getAttribute('data-categories').split(',');
                const name = card.querySelector('h3').textContent.toLowerCase();
                const description = card.querySelector('.card-description').textContent.toLowerCase();

                const matchesSearch = !searchTerm ||
                    action.includes(searchTerm) ||
                    name.includes(searchTerm) ||
                    description.includes(searchTerm);

                const matchesCategory = !selectedCategory || categories.includes(selectedCategory);

                if (matchesSearch && matchesCategory) {{
                    card.parentElement.style.display = 'block';
                    visibleCount++;
                }} else {{
                    card.parentElement.style.display = 'none';
                }}
            }});

            resultCount.textContent = `Showing ${{visibleCount}} action${{visibleCount !== 1 ? 's' : ''}}`;
        }}

        searchInput.addEventListener('input', filterActions);
        categoryFilter.addEventListener('change', filterActions);
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
    --danger: #d1242f;
    --warning: #9e6a03;
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

.action-card-link {
    text-decoration: none;
    color: inherit;
    display: block;
    height: 100%;
}

.action-card-link:hover {
    text-decoration: none;
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
    height: 100%;
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

.card-title-section {
    flex: 1;
}

.card-header h3 {
    font-size: 1.1rem;
    margin: 0;
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
}

.card-categories {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.card-link {
    color: var(--primary);
    font-weight: 500;
    margin-top: auto;
}

.action-card:hover .card-link {
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

.badge-category {
    background: var(--gray-200);
    color: var(--gray-800);
}

.badge-verified {
    background: var(--success);
    color: white;
    flex-shrink: 0;
}

.badge-more {
    background: var(--gray-300);
    color: var(--gray-800);
}

/* Detail page styles */
.back-link {
    display: inline-block;
    color: var(--primary);
    text-decoration: none;
    margin-bottom: 1.5rem;
}

.back-link:hover {
    text-decoration: underline;
}

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.detail-header h1 {
    margin: 0;
}

.detail-meta {
    background: var(--gray-100);
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.detail-meta p {
    margin: 0.5rem 0;
}

.detail-meta code {
    background: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    border: 1px solid var(--gray-200);
}

.section {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid var(--gray-200);
}

.section h2,
.section h3 {
    margin: 0 0 1rem 0;
}

.inputs-table,
.outputs-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.inputs-table thead,
.outputs-table thead {
    background: var(--gray-100);
}

.inputs-table th,
.outputs-table th {
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid var(--gray-200);
}

.inputs-table td,
.outputs-table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-200);
}

.inputs-table code,
.outputs-table code {
    background: var(--gray-100);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
}

.tag {
    display: inline-block;
    background: var(--gray-200);
    color: var(--gray-800);
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.9rem;
    margin-right: 0.5rem;
}

footer {
    background: var(--gray-900);
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
}

footer a {
    color: var(--primary);
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
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

    .detail-header {
        flex-direction: column;
        align-items: flex-start;
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

    # Verify file was written
    css_file = DOCS_DIR / "styles.css"
    if css_file.exists():
        file_size = css_file.stat().st_size
        print(f"   ✅ styles.css ({file_size} bytes)")
    else:
        print("   ❌ styles.css failed to write!")
        return

    # Generate detail pages for each action
    print("📄 Generating detail pages...")
    for i, action in enumerate(actions, 1):
        action_id = action.get("action_id", "")
        sanitized_id = action_id.replace("/", "__")

        detail_html = generate_action_detail(action)
        detail_file = DOCS_DIR / f"{sanitized_id}.html"
        with open(detail_file, "w") as f:
            f.write(detail_html)

        if i % 10 == 0:
            print(f"   ✅ {i}/{len(actions)} detail pages")

    print(f"   ✅ {len(actions)} detail pages")

    # Generate metadata
    print("📄 Generating metadata.json...")
    metadata = {
        "generated_at": datetime.now().isoformat() + "Z",
        "total_actions": len(actions),
        "categories": get_all_categories(actions),
        "verified_publishers": len(set(a["source"]["publisher"] for a in actions if a["source"].get("verified", False)))
    }
    with open(DOCS_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("   ✅ metadata.json")

    print(f"\n✅ Website generated successfully!")
    print(f"📁 Output: {DOCS_DIR.relative_to(Path.cwd())}/")
    print(f"🚀 Ready for GitHub Pages deployment")

if __name__ == "__main__":
    main()
