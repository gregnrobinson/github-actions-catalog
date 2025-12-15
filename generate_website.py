#!/usr/bin/env python3
"""
Generate static HTML website from action catalog.
Outputs to docs/ directory for GitHub Pages deployment.
"""

import json
from pathlib import Path
from datetime import datetime
import html

# Use current working directory
CATALOG_DIR = Path.cwd() / "catalog"
DOCS_DIR = Path.cwd() / "docs"

def escape_html(text):
    """Escape HTML special characters."""
    if text is None:
        return ""
    return html.escape(str(text))

def load_catalog():
    """Load all action catalog entries."""
    actions = []

    if not CATALOG_DIR.exists():
        print(f"⚠️  {CATALOG_DIR} not found")
        return actions

    for entry_dir in CATALOG_DIR.iterdir():
        if not entry_dir.is_dir():
            continue

        latest_file = entry_dir / "latest.json"
        if not latest_file.exists():
            continue

        try:
            with open(latest_file, "r") as f:
                action = json.load(f)
                actions.append(action)
        except Exception as e:
            print(f"⚠️  Failed to load {latest_file}: {e}")

    return actions

def load_action_yml(action):
    """Load the raw action.yml content for display."""
    source = action.get("source", {})
    action_yml_path = source.get("action_yml_path")

    if not action_yml_path:
        return None

    yml_path = Path.cwd() / action_yml_path
    if not yml_path.exists():
        return None

    try:
        with open(yml_path, "r") as f:
            return f.read()
    except Exception:
        return None

def format_date(iso_date):
    """Format ISO date to readable format."""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return iso_date

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
    latest_release = source.get("latest_release")

    # Load action.yml
    action_yml = load_action_yml(action)

    # Build latest release section
    release_html = ""
    if latest_release:
        tag_name = latest_release.get("tag_name", "")
        release_name = latest_release.get("name", tag_name)
        published_at = latest_release.get("published_at", "")
        html_url = latest_release.get("html_url", "")
        prerelease = latest_release.get("prerelease", False)
        draft = latest_release.get("draft", False)

        formatted_date = format_date(published_at)

        # Release badge
        release_badge = ""
        if prerelease:
            release_badge = '<span class="badge badge-prerelease">Pre-release</span>'
        elif draft:
            release_badge = '<span class="badge badge-draft">Draft</span>'
        else:
            release_badge = '<span class="badge badge-release">Latest Release</span>'

        release_html = f'''<div class="modal-section release-section">
            <h3>📦 Latest Release</h3>
            <div class="release-info">
                <div class="release-header">
                    <a href="{escape_html(html_url)}" target="_blank" class="release-title">
                        <strong>{escape_html(release_name)}</strong>
                    </a>
                    {release_badge}
                </div>
                <div class="release-meta">
                    <span class="release-tag">🏷️ {escape_html(tag_name)}</span>
                    <span class="release-date">📅 {escape_html(formatted_date)}</span>
                </div>
                <a href="{escape_html(html_url)}" target="_blank" class="release-link">View Release Notes →</a>
            </div>
        </div>'''

    # Build inputs section
    inputs_html = ""
    if inputs:
        inputs_html = '<div class="section"><h3>Inputs</h3><table class="inputs-table"><thead><tr><th>Name</th><th>Required</th><th>Description</th></tr></thead><tbody>'
        for inp in inputs:
            required_badge = '<span class="badge-required">Required</span>' if inp.get("required") else '<span class="badge-optional">Optional</span>'
            default_value = inp.get("default")
            default_html = f'<div class="input-default">Default: <code>{escape_html(default_value)}</code></div>' if default_value else ''
            inputs_html += f'''<tr>
                <td><code>{escape_html(inp.get("name", ""))}</code></td>
                <td>{required_badge}</td>
                <td>{escape_html(inp.get("description", ""))}{default_html}</td>
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
        categories_html = f'<div class="section"><h3>Categories</h3><div class="modal-categories">{category_badges}</div></div>'

    # Build action.yml section
    action_yml_html = ""
    if action_yml:
        action_yml_escaped = escape_html(action_yml)
        action_yml_html = f'''<div class="section">
            <h3>action.yml</h3>
            <pre><code>{action_yml_escaped}</code></pre>
        </div>'''

    # Build origin link
    origin_html = ""
    if origin:
        origin_html = f'<p><strong>Repository:</strong> <a href="https://{escape_html(origin)}" target="_blank">{escape_html(origin)}</a></p>'

    return f'''
    <div id="modal-{escape_html(sanitized_id)}" class="modal" data-action="{escape_html(action_id)}">
        <div class="modal-content">
            <span class="close">&times;</span>

            <h1>{escape_html(name or action_id)}</h1>

            <div class="modal-section modal-info-section">
                <p><strong>Action ID:</strong> <code>{escape_html(action_id)}</code></p>
                <p><strong>Author:</strong> {escape_html(author or "Unknown")}</p>
                <p><strong>Publisher:</strong> {escape_html(publisher or "internal")}</p>
                {origin_html}
            </div>

            {release_html}

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

def generate_index(actions):
    """Generate the main index.html page."""
    # Calculate statistics
    total_actions = len(actions)
    marketplace_count = sum(1 for a in actions if a.get("source", {}).get("type") == "marketplace")
    internal_count = sum(1 for a in actions if a.get("source", {}).get("type") == "internal")
    verified_count = sum(1 for a in actions if a.get("source", {}).get("verified"))

    # Get all unique categories
    all_categories = set()
    for action in actions:
        categories = action.get("annotations", {}).get("categories", [])
        all_categories.update(categories)
    all_categories = sorted(all_categories)

    # Generate category options
    category_options = '<option value="">All Categories</option>'
    for cat in all_categories:
        category_options += f'<option value="{escape_html(cat)}">{escape_html(cat)}</option>'

    # Create JSON data for all actions
    actions_data = []
    for action in actions:
        action_id = action.get("action_id", "")
        definition = action.get("definition", {})
        source = action.get("source", {})
        annotations = action.get("annotations", {})

        actions_data.append({
            "id": action_id,
            "name": definition.get("name", ""),
            "description": definition.get("description", ""),
            "author": definition.get("author", ""),
            "publisher": source.get("publisher", ""),
            "verified": source.get("verified", False),
            "type": source.get("type", ""),
            "categories": annotations.get("categories", []),
            "sanitized_id": action_id.replace("/", "__")
        })

    actions_json = json.dumps(actions_data)

    # Generate modals for all actions
    modals_html = ""
    for action in actions:
        modals_html += generate_action_modal(action)

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
        <div class="container navbar-content">
            <div class="navbar-left">
                <a href="index.html" class="navbar-brand">🚀 Github Actions Catalog</a>
                <p class="navbar-subtitle">Discover and explore GitHub Actions</p>
            </div>
            <div style="display: flex; gap: 1rem;">
                <a href="workflow-builder.html" class="navbar-btn">🔨 Workflow Builder</a>
                <a href="dependency-visualizer.html" class="navbar-btn">🔗 Workflow Visualizer</a>
            </div>
        </div>
    </nav>

    <main class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_actions}</div>
                <div class="stat-label">Total Actions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{marketplace_count}</div>
                <div class="stat-label">Marketplace</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{internal_count}</div>
                <div class="stat-label">Internal</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{verified_count}</div>
                <div class="stat-label">Verified</div>
            </div>
        </div>

        <div class="search-section">
            <input type="text" id="searchInput" class="search-input" placeholder="Search actions by name, description, or author...">
            <div class="filter-group">
                <select id="categoryFilter" class="category-filter">
                    {category_options}
                </select>
                <select id="typeFilter" class="category-filter">
                    <option value="">All Types</option>
                    <option value="marketplace">Marketplace</option>
                    <option value="internal">Internal</option>
                </select>
            </div>
        </div>

        <div class="results-info" id="resultsInfo">
            Showing {total_actions} actions
        </div>

        <div class="actions-grid" id="actionsGrid"></div>
    </main>

    {modals_html}

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
    </footer>

    <script>
        const allActions = {actions_json};
        let filteredActions = [...allActions];

        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const typeFilter = document.getElementById('typeFilter');
        const actionsGrid = document.getElementById('actionsGrid');
        const resultsInfo = document.getElementById('resultsInfo');
        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.close');

        function renderActions() {{
            actionsGrid.innerHTML = '';

            if (filteredActions.length === 0) {{
                actionsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--dark-text-secondary);">No actions found</div>';
                resultsInfo.textContent = 'No actions found';
                return;
            }}

            resultsInfo.textContent = `Showing ${{filteredActions.length}} action${{filteredActions.length !== 1 ? 's' : ''}}`;

            filteredActions.forEach(action => {{
                const card = document.createElement('div');
                card.className = 'action-card';

                const verifiedBadge = action.verified ? '<span class="badge badge-verified">✓ Verified</span>' : '';
                const typeBadge = action.type === 'marketplace'
                    ? '<span class="badge badge-marketplace">Marketplace</span>'
                    : '<span class="badge badge-internal">Internal</span>';

                const categoryBadges = action.categories.slice(0, 2).map(cat =>
                    `<span class="badge badge-category-primary">${{cat}}</span>`
                ).join('');

                const moreBadge = action.categories.length > 2
                    ? `<span class="badge badge-more">+${{action.categories.length - 2}} more</span>`
                    : '';

                card.innerHTML = `
                    <div class="card-header">
                        <h3>${{action.name || action.id}}</h3>
                    </div>
                    <p class="card-description">${{action.description || 'No description available'}}</p>
                    <div class="card-meta">
                        <strong>Author:</strong> ${{action.author || 'Unknown'}}
                    </div>
                    <div class="card-badges">
                        ${{verifiedBadge}}
                        ${{typeBadge}}
                        ${{categoryBadges}}
                        ${{moreBadge}}
                    </div>
                    <a href="#" class="card-link">View Details →</a>
                `;

                card.addEventListener('click', (e) => {{
                    e.preventDefault();
                    openModal(action.sanitized_id);
                }});

                actionsGrid.appendChild(card);
            }});
        }}

        function filterActions() {{
            const searchTerm = searchInput.value.toLowerCase();
            const selectedCategory = categoryFilter.value;
            const selectedType = typeFilter.value;

            filteredActions = allActions.filter(action => {{
                const matchesSearch = !searchTerm ||
                    action.name.toLowerCase().includes(searchTerm) ||
                    action.description.toLowerCase().includes(searchTerm) ||
                    action.author.toLowerCase().includes(searchTerm) ||
                    action.id.toLowerCase().includes(searchTerm);

                const matchesCategory = !selectedCategory ||
                    action.categories.includes(selectedCategory);

                const matchesType = !selectedType ||
                    action.type === selectedType;

                return matchesSearch && matchesCategory && matchesType;
            }});

            renderActions();
        }}

        function openModal(sanitizedId) {{
            const modal = document.getElementById(`modal-${{sanitizedId}}`);
            if (modal) {{
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }}
        }}

        function closeModal(modal) {{
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }}

        // Event listeners
        searchInput.addEventListener('input', filterActions);
        categoryFilter.addEventListener('change', filterActions);
        typeFilter.addEventListener('change', filterActions);

        closeButtons.forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                const modal = e.target.closest('.modal');
                if (modal) {{
                    closeModal(modal);
                }}
            }});
        }});

        modals.forEach(modal => {{
            modal.addEventListener('click', (e) => {{
                if (e.target === modal) {{
                    closeModal(modal);
                }}
            }});
        }});

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                modals.forEach(modal => {{
                    if (modal.style.display === 'block') {{
                        closeModal(modal);
                    }}
                }});
            }}
        }});

        // Initial render
        renderActions();
    </script>
</body>
</html>'''

def generate_workflow_builder():
    """Generate workflow builder page."""
    actions = load_catalog()

    # Create JSON data for all actions
    actions_data = []
    for action in actions:
        inputs = action.get("definition", {}).get("inputs", [])
        actions_data.append({
            "id": action.get("action_id", ""),
            "name": action.get("definition", {}).get("name", ""),
            "inputs": [{"name": inp.get("name", ""), "description": inp.get("description", ""), "required": inp.get("required", False)} for inp in inputs],
        })

    actions_json = json.dumps(actions_data)

    # Generate modals for all actions
    modals_html = ""
    for action in actions:
        modals_html += generate_action_modal(action)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow Builder - GitHub Actions Catalog</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .workflow-builder {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin: 2rem 0;
        }}

        .builder-sidebar {{
            background: var(--dark-bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--dark-border);
            height: fit-content;
            max-height: 600px;
            display: flex;
            flex-direction: column;
        }}

        .builder-main {{
            background: var(--dark-bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--dark-border);
            min-height: 500px;
        }}

        .action-search {{
            margin-bottom: 1.5rem;
            flex-shrink: 0;
        }}

        .action-search input {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--dark-border);
            border-radius: 6px;
            background: var(--dark-bg);
            color: var(--dark-text);
        }}

        .available-actions {{
            flex: 1;
            overflow-y: auto;
            min-height: 300px;
        }}

        .available-action {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--dark-bg);
            border: 1px solid var(--dark-border);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .available-action:hover {{
            border-color: var(--primary);
            background: var(--dark-bg-tertiary);
        }}

        .available-action-name {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }}

        .available-action-id {{
            font-size: 0.85rem;
            color: var(--dark-text-secondary);
        }}

        .workflow-code {{
            padding: 1rem;
            background: var(--dark-bg);
            border: 1px solid var(--dark-border);
            border-radius: 6px;
            margin-bottom: 2rem;
        }}

        .workflow-code h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}

        .workflow-yaml {{
            background: var(--dark-bg-secondary);
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85rem;
            line-height: 1.5;
            color: var(--code-blue);
            font-family: 'Courier New', monospace;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--dark-border);
            white-space: pre;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}

        .copy-btn {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 0.75rem;
            font-weight: 500;
        }}

        .copy-btn:hover {{
            background: var(--primary-dark);
        }}

        .workflow-steps {{
            margin-top: 1rem;
        }}

        .workflow-step {{
            padding: 1rem;
            background: var(--dark-bg);
            border: 1px solid var(--dark-border);
            border-radius: 6px;
            margin-bottom: 1rem;
            position: relative;
        }}

        .step-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .step-name {{
            font-weight: 600;
            color: var(--primary);
            flex: 1;
            min-width: 150px;
        }}

        .step-buttons {{
            display: flex;
            gap: 0.5rem;
        }}

        .step-btn {{
            border: none;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .step-remove {{
            background: #da3633;
            color: white;
        }}

        .step-remove:hover {{
            background: #b91c1c;
        }}

        .step-details {{
            background: var(--primary);
            color: white;
        }}

        .step-details:hover {{
            background: var(--primary-dark);
        }}

        .step-collapse {{
            background: var(--dark-bg-tertiary);
            color: var(--dark-text);
            border: 1px solid var(--dark-border);
        }}

        .step-collapse:hover {{
            background: var(--dark-bg-secondary);
            border-color: var(--primary);
        }}

        .step-inputs {{
            margin-top: 0.75rem;
            transition: all 0.3s ease;
        }}

        .step-inputs.collapsed {{
            display: none;
        }}

        .step-input {{
            margin-bottom: 0.75rem;
        }}

        .step-input-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.25rem;
        }}

        .step-input label {{
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--dark-text);
        }}

        .step-input-badge {{
            font-size: 0.75rem;
            padding: 0.15rem 0.5rem;
            border-radius: 3px;
            margin-left: 0.5rem;
        }}

        .step-input-badge.required {{
            background: #da3633;
            color: white;
        }}

        .step-input-badge.optional {{
            background: #3b2667;
            color: #c9d1d9;
        }}

        .step-input input {{
            width: 100%;
            padding: 0.5rem;
            border: 1px solid var(--dark-border);
            border-radius: 4px;
            background: var(--dark-bg-secondary);
            color: var(--dark-text);
            font-size: 0.85rem;
        }}

        .empty-state {{
            text-align: center;
            padding: 3rem 1rem;
            color: var(--dark-text-secondary);
        }}

        @media (max-width: 1024px) {{
            .workflow-builder {{
                grid-template-columns: 1fr;
            }}

            .builder-sidebar {{
                max-height: none;
            }}

            .step-header {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .step-buttons {{
                width: 100%;
            }}

            .step-btn {{
                flex: 1;
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container navbar-content">
            <div class="navbar-left">
                <a href="index.html" class="navbar-brand">🚀 Github Actions Catalog</a>
                <p class="navbar-subtitle">Workflow Builder</p>
            </div>
            <a href="index.html" class="navbar-btn">← Back to Catalog</a>
        </div>
    </nav>

    <main class="container">
        <h1>Workflow Builder</h1>
        <p style="color: var(--dark-text-secondary); margin-bottom: 2rem;">Build GitHub Actions workflows by selecting and configuring actions</p>

        <div class="workflow-builder">
            <div class="builder-sidebar">
                <h3>Available Actions</h3>
                <div class="action-search">
                    <input type="text" id="actionSearch" placeholder="Search actions...">
                </div>
                <div class="available-actions" id="availableActions"></div>
            </div>

            <div class="builder-main">
                <div class="workflow-code">
                    <h3>Generated YAML</h3>
                    <div class="workflow-yaml" id="workflowYaml">name: Generated Workflow
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4</div>
                    <button class="copy-btn" onclick="copyWorkflow()">📋 Copy to Clipboard</button>
                </div>

                <h3 style="margin-top: 2rem; margin-bottom: 1rem;">Workflow Steps</h3>
                <div class="workflow-steps" id="workflowSteps">
                    <div class="empty-state">
                        <p>Select actions from the left to build your workflow</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    {modals_html}

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
    </footer>

    <script>
        const allActions = {actions_json};
        let workflowSteps = [];

        const actionSearchInput = document.getElementById('actionSearch');
        const availableActionsDiv = document.getElementById('availableActions');
        const workflowStepsDiv = document.getElementById('workflowSteps');
        const workflowYamlDiv = document.getElementById('workflowYaml');
        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.close');

        // Close modal functionality
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

        function formatActionUses(actionId) {{
            const parts = actionId.split('/');

            if (parts.length >= 3 && parts[0] === 'marketplace') {{
                // Remove 'marketplace/' prefix
                return `${{parts[1]}}/${{parts.slice(2).join('/')}}@main`;
            }} else if (parts.length >= 2 && parts[0] === 'internal') {{
                // Keep internal/ prefix
                return `${{actionId}}@main`;
            }}

            return `${{actionId}}@main`;
        }}

        function renderAvailableActions(searchTerm = '') {{
            availableActionsDiv.innerHTML = '';

            const filtered = allActions.filter(action =>
                action.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                action.id.toLowerCase().includes(searchTerm.toLowerCase())
            );

            if (filtered.length === 0) {{
                availableActionsDiv.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--dark-text-secondary);">No actions found</div>';
                return;
            }}

            filtered.forEach(action => {{
                const div = document.createElement('div');
                div.className = 'available-action';
                div.innerHTML = `
                    <div class="available-action-name">${{action.name || action.id}}</div>
                    <div class="available-action-id">${{action.id}}</div>
                `;
                div.addEventListener('click', () => addStep(action));
                availableActionsDiv.appendChild(div);
            }});
        }}

        function addStep(action) {{
            const step = {{
                id: action.id,
                name: action.name || action.id,
                inputs: {{}},
                inputs_schema: action.inputs || [],
                sanitized_id: action.id.replace(/\\//g, '__'),
                collapsed: false
            }};

            workflowSteps.push(step);
            renderWorkflow();
        }}

        function removeStep(index) {{
            workflowSteps.splice(index, 1);
            renderWorkflow();
        }}

        function toggleCollapse(index) {{
            workflowSteps[index].collapsed = !workflowSteps[index].collapsed;
            renderWorkflow();
        }}

        function viewDetails(stepIndex) {{
            const step = workflowSteps[stepIndex];
            const modal = document.getElementById(`modal-${{step.sanitized_id}}`);
            if (modal) {{
                modal.style.display = 'block';
            }}
        }}

        function updateStepInput(stepIndex, inputName, value) {{
            workflowSteps[stepIndex].inputs[inputName] = value;
            renderWorkflow();
        }}

        function renderWorkflow() {{
            const isEmpty = workflowSteps.length === 0;

            if (isEmpty) {{
                workflowStepsDiv.innerHTML = '<div class="empty-state"><p>Select actions from the left to build your workflow</p></div>';
            }} else {{
                workflowStepsDiv.innerHTML = '';
                workflowSteps.forEach((step, index) => {{
                    const stepDiv = document.createElement('div');
                    stepDiv.className = 'workflow-step';

                    let inputsHtml = '';
                    if (step.inputs_schema && step.inputs_schema.length > 0) {{
                        const collapsedClass = step.collapsed ? 'collapsed' : '';
                        inputsHtml = `<div class="step-inputs ${{collapsedClass}}">`;
                        step.inputs_schema.forEach(input => {{
                            const value = step.inputs[input.name] || '';
                            const isRequired = input.required ? 'required' : 'optional';
                            const badgeText = input.required ? 'Required' : 'Optional';
                            inputsHtml += `
                                <div class="step-input">
                                    <div class="step-input-header">
                                        <label>${{input.name}}</label>
                                        <span class="step-input-badge ${{isRequired}}">${{badgeText}}</span>
                                    </div>
                                    <input type="text" value="${{value}}" placeholder="${{input.description || ''}}"
                                        onchange="updateStepInput(${{index}}, '${{input.name}}', this.value)">
                                </div>
                            `;
                        }});
                        inputsHtml += '</div>';
                    }}

                    const collapseIcon = step.collapsed ? '▶' : '▼';
                    const collapseText = step.collapsed ? 'Expand' : 'Collapse';
                    const collapseBtn = step.inputs_schema && step.inputs_schema.length > 0
                        ? `<button class="step-btn step-collapse" onclick="toggleCollapse(${{index}})">${{collapseIcon}} ${{collapseText}}</button>`
                        : '';

                    stepDiv.innerHTML = `
                        <div class="step-header">
                            <div class="step-name">Step ${{index + 1}}: ${{step.name}}</div>
                            <div class="step-buttons">
                                ${{collapseBtn}}
                                <button class="step-btn step-details" onclick="viewDetails(${{index}})">ℹ️ Details</button>
                                <button class="step-btn step-remove" onclick="removeStep(${{index}})">Remove</button>
                            </div>
                        </div>
                        ${{inputsHtml}}
                    `;
                    workflowStepsDiv.appendChild(stepDiv);
                }});
            }}

            generateYaml();
        }}

        function generateYaml() {{
            let lines = [];
            lines.push('name: Generated Workflow');
            lines.push('on: [push, pull_request]');
            lines.push('');
            lines.push('jobs:');
            lines.push('  build:');
            lines.push('    runs-on: ubuntu-latest');
            lines.push('    steps:');
            lines.push('      - uses: actions/checkout@v4');

            workflowSteps.forEach((step, index) => {{
                lines.push(`      - name: ${{step.name}}`);
                lines.push(`        uses: ${{formatActionUses(step.id)}}`);

                if (Object.keys(step.inputs).length > 0) {{
                    lines.push('        with:');
                    Object.entries(step.inputs).forEach(([key, value]) => {{
                        if (value) {{
                            lines.push(`          ${{key}}: ${{value}}`);
                        }}
                    }});
                }}
            }});

            const yaml = lines.join('\\n');
            workflowYamlDiv.textContent = yaml;
        }}

        function copyWorkflow() {{
            const yaml = workflowYamlDiv.textContent;
            navigator.clipboard.writeText(yaml).then(() => {{
                alert('✅ Workflow copied to clipboard!');
            }}).catch(() => {{
                alert('❌ Failed to copy');
            }});
        }}

        actionSearchInput.addEventListener('input', (e) => {{
            renderAvailableActions(e.target.value);
        }});

        // Initial render
        renderAvailableActions();
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
    --primary: #58a6ff;
    --primary-dark: #1f6feb;
    --success: #3fb950;
    --dark-bg: #0d1117;
    --dark-bg-secondary: #161b22;
    --dark-bg-tertiary: #21262d;
    --dark-border: #30363d;
    --dark-text: #c9d1d9;
    --dark-text-secondary: #8b949e;
    --gray-300: #d0d7de;
    --code-blue: #79c0ff;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--dark-text);
    background: var(--dark-bg);
}

.navbar {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    color: white;
    padding: 2rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--dark-border);
}

.navbar-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-left {
    flex: 1;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: 600;
    text-decoration: none;
    color: var(--primary);
}

.navbar-subtitle {
    font-size: 0.9rem;
    opacity: 0.8;
    margin-top: 0.5rem;
    color: var(--dark-text-secondary);
}

.navbar-btn {
    background: var(--primary);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
}

.navbar-btn:hover {
    background: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--dark-bg-secondary);
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--dark-border);
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.stat-number {
    font-size: 2rem;
    font-weight: 600;
    color: var(--primary);
}

.stat-label {
    color: var(--dark-text-secondary);
    font-size: 0.9rem;
    margin-top: 0.5rem;
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
    border: 1px solid var(--dark-border);
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.2s;
    background: var(--dark-bg-secondary);
    color: var(--dark-text);
}

.search-input::placeholder {
    color: var(--dark-text-secondary);
}

.search-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
}

.filter-group {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.category-filter {
    padding: 0.75rem 1rem;
    border: 1px solid var(--dark-border);
    border-radius: 6px;
    font-size: 1rem;
    background: var(--dark-bg-secondary);
    color: var(--dark-text);
    cursor: pointer;
    transition: border-color 0.2s;
}

.category-filter:focus {
    outline: none;
    border-color: var(--primary);
}

.results-info {
    margin-bottom: 1.5rem;
    color: var(--dark-text-secondary);
}

.actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.action-card {
    background: var(--dark-bg-secondary);
    border: 1px solid var(--dark-border);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.2s;
    cursor: pointer;
    display: flex;
    flex-direction: column;
}

.action-card:hover {
    border-color: var(--primary);
    box-shadow: 0 3px 12px rgba(88, 166, 255, 0.15);
    transform: translateY(-2px);
    background: var(--dark-bg-tertiary);
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
    color: var(--primary);
}

.card-description {
    color: var(--dark-text-secondary);
    margin-bottom: 1rem;
    flex-grow: 1;
}

.card-meta {
    margin-bottom: 1rem;
    color: var(--dark-text-secondary);
    font-size: 0.9rem;
}

.card-badges {
    display: flex;
    column-gap: 0.5rem;
    row-gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    align-items: center;
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
    margin: 0;
}

.badge-category-primary {
    background: #3b2667;
    color: #c9d1d9;
    font-weight: 600;
}

.badge-verified {
    background: var(--success);
    color: white;
}

.badge-internal {
    background: #3b2667;
    color: #c9d1d9;
}

.badge-marketplace {
    background: #1f6feb;
    color: white;
}

.badge-more {
    background: var(--dark-bg-tertiary);
    color: var(--dark-text);
    border: 1px solid var(--dark-border);
}

.badge-required {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #da3633;
    color: white;
    margin: 0;
}

.badge-optional {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #3b2667;
    color: #c9d1d9;
    margin: 0;
}

.badge-release {
    background: var(--success);
    color: white;
}

.badge-prerelease {
    background: #ffa657;
    color: #0d1117;
}

.badge-draft {
    background: var(--dark-border);
    color: var(--dark-text);
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.6);
    overflow-y: auto;
}

.modal-content {
    background: var(--dark-bg-secondary);
    margin: 2rem auto;
    padding: 2rem;
    border-radius: 8px;
    max-width: 900px;
    max-height: 90vh;
    overflow-y: auto;
    border: 1px solid var(--dark-border);
}

.close {
    color: var(--dark-text-secondary);
    float: right;
    font-size: 2rem;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: var(--dark-text);
}

.modal-content h1 {
    margin: 0 0 1rem 0;
    font-size: 1.8rem;
    color: var(--primary);
}

.modal-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
}

.modal-info-section p {
    margin: 0.35rem 0;
}

.modal-section p {
    margin: 0.0rem 0;
}

.modal-section p:first-child {
    margin-top: 0;
}

.modal-section:last-child {
    border-bottom: none;
}

.modal-section h2,
.modal-section h3 {
    margin: 0 0 1rem 0;
    color: var(--primary);
}

.modal-section a {
    color: var(--code-blue);
}

.modal-section a:hover {
    text-decoration: underline;
}

.modal-section .badge {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

.modal-categories {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.release-section {
    background: var(--dark-bg-tertiary);
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--dark-border);
}

.release-info {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.release-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.release-title {
    font-size: 1.1rem;
    color: var(--primary);
    text-decoration: none;
}

.release-title:hover {
    text-decoration: underline;
}

.release-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    color: var(--dark-text-secondary);
    font-size: 0.9rem;
}

.release-tag,
.release-date {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.release-link {
    display: inline-block;
    color: var(--primary);
    font-weight: 500;
    text-decoration: none;
    margin-top: 0.5rem;
}

.release-link:hover {
    text-decoration: underline;
}

.section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
}

.section:last-child {
    border-bottom: none;
}

.section h3 {
    margin: 0 0 1rem 0;
    color: var(--primary);
}

.input-default {
    margin-top: 0.25rem;
    font-size: 0.85rem;
    color: var(--dark-text-secondary);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--dark-border);
}

th {
    background: var(--dark-bg-tertiary);
    font-weight: 600;
}

code {
    background: var(--dark-bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    color: var(--code-blue);
}

pre {
    background: var(--dark-bg);
    color: var(--dark-text);
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin-top: 1rem;
    border: 1px solid var(--dark-border);
}

pre code {
    background: none;
    padding: 0;
    color: inherit;
    font-size: 0.9rem;
}

footer {
    background: var(--dark-bg-secondary);
    color: var(--dark-text-secondary);
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
    border-top: 1px solid var(--dark-border);
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

    .navbar-content {
        flex-direction: column;
        gap: 1rem;
        align-items: flex-start;
    }

    .navbar-btn {
        width: 100%;
        text-align: center;
    }

    .release-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .release-meta {
        flex-direction: column;
        gap: 0.5rem;
    }
}
'''

def generate_dependency_visualizer():
    """Generate dependency graph visualizer page."""
    actions = load_catalog()

    # Generate modals for all actions
    modals_html = ""
    for action in actions:
        modals_html += generate_action_modal(action)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Visualizer - GitHub Actions Catalog</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        .dependency-visualizer {{
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 1.5rem;
            margin: 2rem 0;
            height: calc(100vh - 200px);
        }}

        .visualizer-sidebar {{
            background: var(--dark-bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--dark-border);
            overflow-y: auto;
        }}

        .visualizer-main {{
            background: var(--dark-bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--dark-border);
            position: relative;
            overflow: hidden;
        }}

        .graph-container {{
            width: 100%;
            height: 100%;
            position: relative;
        }}

        #graph {{
            width: 100%;
            height: 100%;
        }}

        .controls {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
            z-index: 10;
        }}

        .control-btn {{
            background: var(--dark-bg-tertiary);
            border: 1px solid var(--dark-border);
            color: var(--dark-text);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}

        .control-btn:hover {{
            background: var(--dark-bg);
            border-color: var(--primary);
        }}

        .control-btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        .node {{
            cursor: pointer;
            transition: all 0.3s;
        }}

        .node circle {{
            fill: var(--dark-bg-tertiary);
            stroke: var(--primary);
            stroke-width: 2px;
        }}

        .node.selected circle {{
            fill: var(--primary);
            stroke: var(--primary-dark);
            stroke-width: 3px;
        }}

        .node.dependency circle {{
            fill: #ffa657;
            stroke: #ff8c00;
        }}

        .node.dependent circle {{
            fill: var(--success);
            stroke: #2eb886;
        }}

        .node text {{
            fill: var(--dark-text);
            font-size: 12px;
            pointer-events: none;
            text-anchor: middle;
        }}

        .link {{
            fill: none;
            stroke: var(--dark-border);
            stroke-width: 2px;
            marker-end: url(#arrowhead);
        }}

        .link.selected {{
            stroke: var(--primary);
            stroke-width: 3px;
        }}

        .link.circular {{
            stroke: #da3633;
            stroke-width: 3px;
            stroke-dasharray: 5,5;
            animation: dash 1s linear infinite;
        }}

        @keyframes dash {{
            to {{
                stroke-dashoffset: -10;
            }}
        }}

        .legend {{
            position: absolute;
            bottom: 1rem;
            left: 1rem;
            background: var(--dark-bg-tertiary);
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid var(--dark-border);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }}

        .legend-item:last-child {{
            margin-bottom: 0;
        }}

        .legend-circle {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid;
        }}

        .workflow-list {{
            max-height: calc(100vh - 400px);
            overflow-y: auto;
        }}

        .workflow-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--dark-bg);
            border: 1px solid var(--dark-border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .workflow-item:hover {{
            border-color: var(--primary);
            background: var(--dark-bg-tertiary);
        }}

        .workflow-item.active {{
            border-color: var(--primary);
            background: var(--dark-bg-tertiary);
        }}

        .workflow-name {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }}

        .workflow-steps {{
            font-size: 0.85rem;
            color: var(--dark-text-secondary);
        }}

        .stats {{
            background: var(--dark-bg);
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid var(--dark-border);
            margin-bottom: 1rem;
        }}

        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }}

        .stat-item:last-child {{
            margin-bottom: 0;
        }}

        .stat-label {{
            color: var(--dark-text-secondary);
        }}

        .stat-value {{
            color: var(--primary);
            font-weight: 600;
        }}

        .warning {{
            background: rgba(218, 54, 51, 0.1);
            border: 1px solid #da3633;
            padding: 0.75rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            color: #da3633;
            font-size: 0.85rem;
        }}

        @media (max-width: 1024px) {{
            .dependency-visualizer {{
                grid-template-columns: 1fr;
            }}

            .visualizer-sidebar {{
                max-height: 300px;
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container navbar-content">
            <div class="navbar-left">
                <a href="index.html" class="navbar-brand">🚀 Github Actions Catalog</a>
                <p class="navbar-subtitle">Dependency Visualizer</p>
            </div>
            <a href="index.html" class="navbar-btn">← Back to Catalog</a>
        </div>
    </nav>

    <main class="container">
        <h1>Workflow Dependency Visualizer</h1>
        <p style="color: var(--dark-text-secondary); margin-bottom: 2rem;">
            Visualize action dependencies and identify potential circular references in your workflows
        </p>

        <div class="dependency-visualizer">
            <div class="visualizer-sidebar">
                <h3>Workflows</h3>

                <div class="stats" id="stats">
                    <div class="stat-item">
                        <span class="stat-label">Total Steps:</span>
                        <span class="stat-value">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Workflow Visualizer:</span>
                        <span class="stat-value">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Max Depth:</span>
                        <span class="stat-value">0</span>
                    </div>
                </div>

                <div id="warnings"></div>

                <div class="workflow-list" id="workflowList">
                    <div class="workflow-item active" data-workflow="sample">
                        <div class="workflow-name">Sample CI/CD Workflow</div>
                        <div class="workflow-steps">7 steps</div>
                    </div>
                </div>
            </div>

            <div class="visualizer-main">
                <div class="controls">
                    <button class="control-btn" onclick="resetZoom()">🔍 Reset View</button>
                    <button class="control-btn" onclick="centerGraph()">🎯 Center</button>
                    <button class="control-btn" onclick="exportSVG()">💾 Export SVG</button>
                    <button class="control-btn" onclick="exportPNG()">📷 Export PNG</button>
                    <button class="control-btn" id="layoutBtn" onclick="toggleLayout()">📊 Tree Layout</button>
                </div>

                <div class="graph-container">
                    <svg id="graph"></svg>
                </div>

                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-circle" style="background: var(--dark-bg-tertiary); border-color: var(--primary);"></div>
                        <span>Normal Step</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: var(--primary); border-color: var(--primary-dark);"></div>
                        <span>Selected Step</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #ffa657; border-color: #ff8c00;"></div>
                        <span>Dependency</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: var(--success); border-color: #2eb886;"></div>
                        <span>Dependent</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    {modals_html}

    <footer>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
    </footer>

    <script>
        const workflows = {{
            sample: {{
                name: "Sample CI/CD Workflow",
                nodes: [
                    {{ id: "checkout", label: "Checkout", type: "action" }},
                    {{ id: "setup-node", label: "Setup Node", type: "action" }},
                    {{ id: "install", label: "Install Dependencies", type: "action" }},
                    {{ id: "lint", label: "Lint", type: "action" }},
                    {{ id: "test", label: "Test", type: "action" }},
                    {{ id: "build", label: "Build", type: "action" }},
                    {{ id: "deploy", label: "Deploy", type: "action" }}
                ],
                links: [
                    {{ source: "checkout", target: "setup-node" }},
                    {{ source: "setup-node", target: "install" }},
                    {{ source: "install", target: "lint" }},
                    {{ source: "install", target: "test" }},
                    {{ source: "lint", target: "build" }},
                    {{ source: "test", target: "build" }},
                    {{ source: "build", target: "deploy" }}
                ]
            }}
        }};

        let currentWorkflow = "sample";
        let currentLayout = "force";
        let svg, g, simulation, zoom;
        let selectedNode = null;

        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.close');

        closeButtons.forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                const modal = e.target.closest('.modal');
                if (modal) {{
                    modal.style.display = 'none';
                }}
            }});
        }});

        modals.forEach(modal => {{
            modal.addEventListener('click', (e) => {{
                if (e.target === modal) {{
                    modal.style.display = 'none';
                }}
            }});
        }});

        function initGraph() {{
            const container = d3.select("#graph");
            const width = container.node().getBoundingClientRect().width;
            const height = container.node().getBoundingClientRect().height;

            svg = container
                .attr("width", width)
                .attr("height", height);

            svg.append("defs").append("marker")
                .attr("id", "arrowhead")
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 25)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "var(--dark-border)");

            zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }});

            svg.call(zoom);
            g = svg.append("g");

            renderGraph();
        }}

        function renderGraph() {{
            const workflow = workflows[currentWorkflow];
            const nodes = JSON.parse(JSON.stringify(workflow.nodes));
            const links = JSON.parse(JSON.stringify(workflow.links));

            g.selectAll("*").remove();

            const circular = detectCircularDependencies(nodes, links);
            if (circular.length > 0) {{
                showWarning(`⚠️ Circular dependencies detected: ${{circular.join(", ")}}`);
            }} else {{
                hideWarning();
            }}

            updateStats(nodes.length, links.length, calculateMaxDepth(nodes, links));

            if (currentLayout === "force") {{
                renderForceLayout(nodes, links);
            }} else {{
                renderTreeLayout(nodes, links);
            }}
        }}

        function renderForceLayout(nodes, links) {{
            const width = svg.node().getBoundingClientRect().width;
            const height = svg.node().getBoundingClientRect().height;

            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(150))
                .force("charge", d3.forceManyBody().strength(-500))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(50));

            const link = g.append("g")
                .selectAll("path")
                .data(links)
                .join("path")
                .attr("class", "link");

            const node = g.append("g")
                .selectAll("g")
                .data(nodes)
                .join("g")
                .attr("class", "node")
                .call(drag(simulation))
                .on("click", (event, d) => handleNodeClick(d));

            node.append("circle")
                .attr("r", 20);

            node.append("text")
                .attr("dy", 30)
                .text(d => d.label);

            simulation.on("tick", () => {{
                link.attr("d", d => {{
                    return `M${{d.source.x}},${{d.source.y}}L${{d.target.x}},${{d.target.y}}`;
                }});

                node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});
        }}

        function renderTreeLayout(nodes, links) {{
            const width = svg.node().getBoundingClientRect().width;
            const height = svg.node().getBoundingClientRect().height;

            const root = d3.stratify()
                .id(d => d.id)
                .parentId(d => {{
                    const parent = links.find(l => l.target === d.id);
                    return parent ? parent.source : null;
                }})(nodes);

            const treeLayout = d3.tree().size([width - 100, height - 100]);
            treeLayout(root);

            const link = g.append("g")
                .selectAll("path")
                .data(root.links())
                .join("path")
                .attr("class", "link")
                .attr("d", d3.linkVertical()
                    .x(d => d.x)
                    .y(d => d.y));

            const node = g.append("g")
                .selectAll("g")
                .data(root.descendants())
                .join("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`)
                .on("click", (event, d) => handleNodeClick(d.data));

            node.append("circle")
                .attr("r", 20);

            node.append("text")
                .attr("dy", 30)
                .text(d => d.data.label);

            const bounds = g.node().getBBox();
            const translateX = (width - bounds.width) / 2 - bounds.x;
            const translateY = 50 - bounds.y;
            g.attr("transform", `translate(${{translateX}},${{translateY}})`);
        }}

        function handleNodeClick(node) {{
            selectedNode = node.id;

            d3.selectAll(".node")
                .classed("selected", false)
                .classed("dependency", false)
                .classed("dependent", false);

            d3.selectAll(".link")
                .classed("selected", false);

            d3.selectAll(".node")
                .filter(d => d.id === node.id || (d.data && d.data.id === node.id))
                .classed("selected", true);

            const workflow = workflows[currentWorkflow];
            const dependencies = workflow.links
                .filter(l => l.target === node.id)
                .map(l => l.source);

            const dependents = workflow.links
                .filter(l => l.source === node.id)
                .map(l => l.target);

            d3.selectAll(".node")
                .filter(d => {{
                    const id = d.id || d.data.id;
                    return dependencies.includes(id);
                }})
                .classed("dependency", true);

            d3.selectAll(".node")
                .filter(d => {{
                    const id = d.id || d.data.id;
                    return dependents.includes(id);
                }})
                .classed("dependent", true);

            d3.selectAll(".link")
                .filter(function() {{
                    const link = d3.select(this).datum();
                    return link.source.id === node.id || link.target.id === node.id ||
                           link.source === node.id || link.target === node.id;
                }})
                .classed("selected", true);
        }}

        function detectCircularDependencies(nodes, links) {{
            const circular = [];
            const visited = new Set();
            const recStack = new Set();

            function dfs(nodeId) {{
                visited.add(nodeId);
                recStack.add(nodeId);

                const neighbors = links
                    .filter(l => l.source === nodeId)
                    .map(l => l.target);

                for (const neighbor of neighbors) {{
                    if (!visited.has(neighbor)) {{
                        if (dfs(neighbor)) {{
                            circular.push(`${{nodeId}} → ${{neighbor}}`);
                            return true;
                        }}
                    }} else if (recStack.has(neighbor)) {{
                        circular.push(`${{nodeId}} → ${{neighbor}}`);
                        return true;
                    }}
                }}

                recStack.delete(nodeId);
                return false;
            }}

            nodes.forEach(node => {{
                if (!visited.has(node.id)) {{
                    dfs(node.id);
                }}
            }});

            return circular;
        }}

        function calculateMaxDepth(nodes, links) {{
            const depths = {{}};
            nodes.forEach(n => depths[n.id] = 0);

            let changed = true;
            while (changed) {{
                changed = false;
                links.forEach(link => {{
                    const newDepth = depths[link.source] + 1;
                    if (newDepth > depths[link.target]) {{
                        depths[link.target] = newDepth;
                        changed = true;
                    }}
                }});
            }}

            return Math.max(...Object.values(depths));
        }}

        function updateStats(nodes, links, depth) {{
            const stats = document.getElementById("stats");
            stats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Total Steps:</span>
                    <span class="stat-value">${{nodes}}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Dependencies:</span>
                    <span class="stat-value">${{links}}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Max Depth:</span>
                    <span class="stat-value">${{depth}}</span>
                </div>
            `;
        }}

        function showWarning(message) {{
            document.getElementById("warnings").innerHTML = `<div class="warning">${{message}}</div>`;
        }}

        function hideWarning() {{
            document.getElementById("warnings").innerHTML = "";
        }}

        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}

            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}

            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}

            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }}

        function resetZoom() {{
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        }}

        function centerGraph() {{
            const bounds = g.node().getBBox();
            const width = svg.node().getBoundingClientRect().width;
            const height = svg.node().getBoundingClientRect().height;
            const scale = 0.9 / Math.max(bounds.width / width, bounds.height / height);
            const translate = [
                width / 2 - scale * (bounds.x + bounds.width / 2),
                height / 2 - scale * (bounds.y + bounds.height / 2)
            ];

            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
        }}

        function toggleLayout() {{
            currentLayout = currentLayout === "force" ? "tree" : "force";
            document.getElementById("layoutBtn").textContent =
                currentLayout === "force" ? "📊 Tree Layout" : "🌐 Force Layout";
            renderGraph();
        }}

        function exportSVG() {{
            const svgData = svg.node().outerHTML;
            const blob = new Blob([svgData], {{ type: "image/svg+xml" }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "workflow-dependency-graph.svg";
            a.click();
            URL.revokeObjectURL(url);
        }}

        function exportPNG() {{
            const svgElement = svg.node();
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const img = new Image();

            canvas.width = svgElement.getBoundingClientRect().width;
            canvas.height = svgElement.getBoundingClientRect().height;

            img.onload = function() {{
                ctx.fillStyle = "#0d1117";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);

                canvas.toBlob(function(blob) {{
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "workflow-dependency-graph.png";
                    a.click();
                    URL.revokeObjectURL(url);
                }});
            }};

            img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
        }}

        window.addEventListener("load", initGraph);
        window.addEventListener("resize", renderGraph);
    </script>
</body>
</html>'''

def main():
    """Generate static website."""
    print("🌐 Generating static website\n")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    actions = load_catalog()
    print(f"Loaded {len(actions)} actions\n")

    print("Generating index.html...")
    index_html = generate_index(actions)
    with open(DOCS_DIR / "index.html", "w") as f:
        f.write(index_html)

    print("Generating workflow-builder.html...")
    workflow_builder_html = generate_workflow_builder()
    with open(DOCS_DIR / "workflow-builder.html", "w") as f:
        f.write(workflow_builder_html)

    print("Generating dependency-visualizer.html...")
    dependency_visualizer_html = generate_dependency_visualizer()
    with open(DOCS_DIR / "dependency-visualizer.html", "w") as f:
        f.write(dependency_visualizer_html)

    print("Generating styles.css...")
    styles_css = generate_styles()
    with open(DOCS_DIR / "styles.css", "w") as f:
        f.write(styles_css)

    print(f"\n✅ Website generated successfully!")
    print(f"📁 Output: {DOCS_DIR.relative_to(Path.cwd())}/")
    print(f"\nFiles created:")
    print(f"  - index.html")
    print(f"  - workflow-builder.html")
    print(f"  - dependency-visualizer.html")
    print(f"  - styles.css")

if __name__ == "__main__":
    main()
