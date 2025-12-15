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

    # Parse action_id: marketplace/publisher/action_name or internal/action_name
    parts = action_id.split("/")

    blueprints_dir = Path.cwd() / "blueprints"

    if len(parts) >= 3 and parts[0] == "marketplace":
        # marketplace/publisher/action_name
        publisher = parts[1]
        action_name = "/".join(parts[2:])  # Handle action names with slashes
        action_yml_path = blueprints_dir / "marketplace" / publisher / action_name / "action.yml"

        if action_yml_path.exists():
            with open(action_yml_path, "r") as f:
                return f.read()

    elif len(parts) >= 2 and parts[0] == "internal":
        # internal/action_name
        action_name = "/".join(parts[1:])
        action_yml_path = blueprints_dir / "internal" / action_name / "action.yml"

        if action_yml_path.exists():
            with open(action_yml_path, "r") as f:
                return f.read()

    return None

def get_catalog_stats(actions):
    """Get catalog statistics."""
    internal_count = 0
    marketplace_count = 0
    verified_count = 0

    for action in actions:
        action_type = get_action_type(action)

        if action_type == "marketplace":
            marketplace_count += 1
        else:
            internal_count += 1

        if action.get("source", {}).get("verified"):
            verified_count += 1

    return {
        "total": len(actions),
        "internal": internal_count,
        "marketplace": marketplace_count,
        "verified": verified_count
    }

def format_action_uses(action_id):
    """Format action ID for uses field in YAML.

    Converts:
    - marketplace/owner/repo -> owner/repo@main
    - internal/action -> internal/action@main
    """
    parts = action_id.split("/")

    if len(parts) >= 3 and parts[0] == "marketplace":
        # Remove 'marketplace/' prefix
        return f"{parts[1]}/{'/'.join(parts[2:])}@main"
    elif len(parts) >= 2 and parts[0] == "internal":
        # Keep internal/ prefix
        return f"{action_id}@main"

    return f"{action_id}@main"

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
            required_badge = '<span class="badge-required">Required</span>' if inp.get("required") else '<span class="badge-optional">Optional</span>'
            inputs_html += f'''<tr>
                <td><code>{escape_html(inp.get("name", ""))}</code></td>
                <td>{required_badge}</td>
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
            <!-- pragma: allowlist secret -->
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
    <title>Workflow Generator - GitHub Actions Catalog</title>
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

        .workflow-steps {{
            margin-bottom: 1.5rem;
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

        .step-inputs {{
            margin-top: 0.75rem;
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

        .workflow-code {{
            margin-top: 2rem;
            padding: 1rem;
            background: var(--dark-bg);
            border: 1px solid var(--dark-border);
            border-radius: 6px;
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
                <p class="navbar-subtitle">Workflow Generator</p>
            </div>
            <a href="index.html" class="navbar-btn">← Back to Catalog</a>
        </div>
    </nav>

    <main class="container">
        <h1>Workflow Generator</h1>
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
                <h3>Workflow Steps</h3>
                <div class="workflow-steps" id="workflowSteps">
                    <div class="empty-state">
                        <p>Select actions from the left to build your workflow</p>
                    </div>
                </div>

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
                sanitized_id: action.id.replace(/\\//g, '__')
            }};

            workflowSteps.push(step);
            renderWorkflow();
        }}

        function removeStep(index) {{
            workflowSteps.splice(index, 1);
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
                        inputsHtml = '<div class="step-inputs">';
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

                    stepDiv.innerHTML = `
                        <div class="step-header">
                            <div class="step-name">Step ${{index + 1}}: ${{step.name}}</div>
                            <div class="step-buttons">
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

def generate_index():
    """Generate main index page."""
    actions = load_catalog()
    categories = get_all_categories(actions)
    stats = get_catalog_stats(actions)

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
        <div class="container navbar-content">
            <div class="navbar-left">
                <a href="index.html" class="navbar-brand">🚀 Github Actions Catalog</a>
                <p class="navbar-subtitle">Browse {stats['total']} GitHub Actions</p>
            </div>
            <a href="workflow-generator.html" class="navbar-btn">⚙️ Build Workflow</a>
        </div>
    </nav>

    <main class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">Total Actions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['internal']}</div>
                <div class="stat-label">Internal Actions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['marketplace']}</div>
                <div class="stat-label">Marketplace Actions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['verified']}</div>
                <div class="stat-label">Verified Publishers</div>
            </div>
        </div>

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
            <p id="resultCount">Showing {stats['total']} actions</p>
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
}

.badge-optional {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #3b2667;
    color: #c9d1d9;
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
}
'''

def main():
    """Generate website."""
    print("🌐 Generating static HTML website for GitHub Pages\n")

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

    # Generate workflow builder
    print("📄 Generating workflow-generator.html...")
    workflow_html = generate_workflow_builder()
    with open(DOCS_DIR / "workflow-generator.html", "w") as f:
        f.write(workflow_html)
    print("   ✅ workflow-generator.html")

    # Generate styles.css
    print("📄 Generating styles.css...")
    styles = generate_styles()
    with open(DOCS_DIR / "styles.css", "w") as f:
        f.write(styles)
    print("   ✅ styles.css")

    print(f"\n✅ Website generated successfully!")
    print(f"📁 Output: {DOCS_DIR.relative_to(Path.cwd())}/")
    print(f"   - index.html (main catalog)")
    print(f"   - workflow-generator.html (build workflows)")
    print(f"   - styles.css (styles)")
    print(f"🚀 Ready for GitHub Pages deployment")

if __name__ == "__main__":
    main()
