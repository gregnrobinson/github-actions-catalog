# 🚀 GitHub Actions Catalog

An internal catalog platform for organizations to host and discover both official internal actions and curated marketplace actions for workflow development.

## 🌐 Live Demo

**[View Live Demo →](https://gregnrobinson.github.io/github-actions-catalog)**

Try the catalog now! Search, filter, and explore actions.

---

## Overview

This project provides your organization with:

- **📚 Unified Action Discovery** - Browse internal actions and marketplace recommendations in one place
- **🏢 Internal Actions Showcase** - Highlight your organization's custom GitHub Actions
- **🔍 Smart Search & Filtering** - Search by name, ID, description, or category
- **✅ Publisher Verification** - Distinguish between internal and marketplace actions
- **📊 Intelligent Categorization** - Automatically categorized for easy discovery
- **🌐 Static Website** - Fast, searchable interface (GitHub Pages or internal hosting)
- **⚡ Auto-Updates** - Automatically refreshes when catalog changes

## Perfect For

✅ **Internal Teams** - Publish and discover company-built actions
✅ **Workflow Developers** - Find approved actions for your CI/CD pipelines
✅ **DevOps Teams** - Centralize action governance and usage
✅ **Multiple Teams** - Share reusable automation across your organization

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- Access to organization repository

### Installation

```bash
git clone https://github.com/your-org/github-actions-catalog.git
cd github-actions-catalog
pip install -r requirements.txt
```

### Building the Catalog

```bash
# Build catalog from blueprint actions
python3 github-actions-catalog/build_catalog.py --no-categorize

# Force update publisher verification status
python3 github-actions-catalog/build_catalog.py --no-categorize --force-publisher-update
```

### Generating the Website

```bash
# Generate static HTML website
cd github-actions-catalog
python3 generate_website.py

# Test locally
cd docs
python3 -m http.server 8000
```

Visit `http://localhost:8000` in your browser.

## Project Structure

```
├── github-actions-catalog/
│   ├── catalog/                 # Generated action catalog
│   │   ├── {action-id}/
│   │   │   ├── latest.json      # Latest action data
│   │   │   └── history/         # Historical versions
│   │   └── metadata.json        # Catalog metadata
│   ├── config/
│   │   ├── blueprint_actions.yaml    # Source action definitions
│   │   └── categorization_config.yaml # Category mappings
│   ├── build_catalog.py         # Catalog builder script
│   ├── generate_website.py      # Website generator
│   └── docs/                    # Generated website (GitHub Pages)
│       ├── index.html           # Main catalog page
│       ├── styles.css           # Styling
│       ├── metadata.json        # Website metadata
│       └── {action-id}.html     # Individual action pages
├── .github/
│   └── workflows/
│       └── generate-pages.yml   # Auto-deploy workflow
└── README.md
```

## Features

### 🔍 Search & Discovery

- **Real-time Search** - Filters as you type
- **Category Filtering** - Browse by action purpose and use case
- **Action Details** - View inputs, outputs, requirements, and documentation
- **Publisher Info** - Identify internal vs. marketplace actions
- **Usage Examples** - See how actions are used in workflows

### 🏢 Internal vs. Marketplace Actions

Actions are clearly marked as:

- **🟢 Internal** - Built by your organization
  - Custom to your workflows
  - Owned by your team
  - Version controlled in your repos

- **🔵 Marketplace** - Official GitHub Actions
  - Pre-vetted and recommended
  - Community maintained
  - Battle-tested by the community

### 📊 Smart Categorization

Actions are organized by:
- **Build** - Compilation, testing, artifact creation
- **Testing** - Test execution, coverage, quality gates
- **Deployment** - Release, publish, promote to production
- **Authentication** - Security, credentials, OIDC
- **Communication** - Notifications, Slack, Teams, email
- **Data** - Processing, analysis, database operations
- **Developer Tools** - Code quality, linting, formatting
- **Monitoring** - Logging, observability, telemetry

### 🌐 Website Features

- **Responsive Design** - Works on desktop, tablet, mobile
- **Fast Performance** - Static HTML, no server needed
- **Offline Capable** - Download and reference locally
- **GitHub Pages Hosted** - Free hosting for public/private repos

## Usage

### For Workflow Developers

#### Finding Actions

1. Visit your organization's Actions Catalog
2. Search for what you need (e.g., "deploy", "test", "notify")
3. Filter by category to narrow results
4. Click "View Details" for usage instructions
5. Copy the action reference into your workflow

#### Using Internal Actions

```yaml
name: Deploy Application

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Use an internal action from your catalog
      - uses: your-org/internal-deploy-action@v1
        with:
          environment: production
          version: ${{ github.ref }}
```

#### Using Marketplace Actions

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '18'
```

### For DevOps/Platform Teams

#### Adding New Internal Actions

1. Build and publish your action to a repository
2. Add entry to `github-actions-catalog/config/blueprint_actions.yaml`
3. Specify as internal in the configuration
4. Run `build_catalog.py` to add to catalog
5. Run `generate_website.py` to update website
6. Commit and push changes

Example internal action:

```yaml
actions:
  - action_id: your-org/deploy-to-aks
    definition:
      name: "Deploy to Azure Kubernetes Service"
      description: "Deploy applications to your organization's AKS clusters"
      author: "Platform Team"
      inputs:
        - name: "cluster-name"
          description: "AKS cluster name"
          required: true
        - name: "namespace"
          description: "Kubernetes namespace"
          required: true
        - name: "image"
          description: "Container image URI"
          required: true
      outputs:
        - name: "deployment-status"
          description: "Status of the deployment"
    source:
      verified: true
      publisher: "your-org"
      origin: "github.com/your-org/actions-deploy-aks"
```

#### Adding Marketplace Actions

Recommend marketplace actions your organization approves:

```yaml
actions:
  - action_id: actions/setup-node
    definition:
      name: "Setup Node.js environment"
      description: "Set up a Node.js environment and add to PATH"
      author: "GitHub"
      inputs:
        - name: "node-version"
          description: "Version of Node.js to use"
          required: false
      outputs:
        - name: "node-version"
          description: "Installed Node.js version"
    source:
      verified: true
      publisher: "GitHub"
      origin: "github.com/actions/setup-node"
```

#### Updating Publisher Status

Force refresh action verification:

```bash
cd github-actions-catalog
python3 build_catalog.py --no-categorize --force-publisher-update
```

## Automation

### GitHub Actions Workflow

The `.github/workflows/generate-pages.yml` workflow automatically:
1. Detects changes to catalog files
2. Rebuilds the website
3. Commits updated `docs/` folder
4. Deploys to GitHub Pages (or internal hosting)

**Requirements:**
- Personal Access Token (PAT) with `repo` and `workflow` scopes
- Stored as `CATALOG_DEPLOY_TOKEN` in repository secrets

## Security

### Scanning for Secrets

Before committing, scan for sensitive information:

```bash
# Install detect-secrets
pip install detect-secrets

# Scan repository
detect-secrets scan .

# Create baseline
detect-secrets scan > .secrets.baseline

# Audit findings
detect-secrets audit .secrets.baseline
```

### Pre-commit Hooks

Install pre-commit hooks to automatically scan on commit:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Access Control

For private catalogs:
- Enable GitHub repository access controls
- Restrict to organization members only
- Set up team-based permissions for catalog updates

## Development

### Building Locally

```bash
# Full rebuild
cd github-actions-catalog
python3 build_catalog.py --no-categorize
python3 generate_website.py

# Test locally
cd docs
python3 -m http.server 8000
```

### Testing Changes

1. Make changes to `blueprint_actions.yaml`
2. Run build and generate scripts
3. Test in local server
4. Commit and push (workflow auto-deploys)

## Deployment

### GitHub Pages Setup (Public/Private Repos)

1. Go to repository Settings
2. Navigate to Pages
3. Set source to "Deploy from a branch"
4. Select `gh-pages` or `main/docs` branch
5. Save

Your catalog will be available at: `https://<org>.github.io/<repo>/`

### Internal Hosting

For air-gapped or fully internal networks:
1. Generate catalog locally
2. Host `docs/` folder on internal web server
3. Distribute link to organization teams

### Custom Domain

To use a custom domain:

1. Add `CNAME` file to `docs/` folder with your domain
2. Configure DNS records
3. Enable HTTPS in repository settings

## API Reference

### Catalog Structure

Each action in the catalog contains:

```json
{
  "action_id": "your-org/action-name",
  "definition": {
    "name": "Display Name",
    "description": "What this action does",
    "author": "Team Name",
    "inputs": [...],
    "outputs": [...]
  },
  "source": {
    "verified": true,
    "publisher": "your-org",
    "origin": "github.com/your-org/repo"
  },
  "annotations": {
    "categories": ["Build", "Deployment"],
    "confidence": "high",
    "evidence": [...]
  }
}
```

### Metadata Files

**docs/metadata.json** - Website statistics:
```json
{
  "generated_at": "2024-12-14T10:30:00Z",
  "total_actions": 344,
  "internal_actions": 45,
  "marketplace_actions": 299,
  "categories": ["Build", "Testing", ...],
  "verified_publishers": 12
}
```

## Troubleshooting

### Website Styling Not Applied

If the website loads but styles aren't visible:

1. Check `docs/styles.css` exists:
   ```bash
   ls -lh github-actions-catalog/docs/styles.css
   ```

2. Regenerate:
   ```bash
   cd github-actions-catalog
   python3 generate_website.py
   ```

3. Check browser console for errors (F12)

### Actions Not Appearing

1. Verify `blueprint_actions.yaml` has valid YAML
2. Check action IDs are unique
3. Rebuild catalog:
   ```bash
   python3 build_catalog.py --no-categorize
   ```

4. Regenerate website:
   ```bash
   python3 generate_website.py
   ```

### Changes Not Deploying

1. Verify `CATALOG_DEPLOY_TOKEN` is set in repository secrets
2. Check workflow file at `.github/workflows/generate-pages.yml`
3. Review workflow run logs for errors
4. Manually trigger workflow if needed

## Contributing

To add actions to the catalog:

1. **For Internal Actions:**
   - Publish action to your organization's GitHub
   - Add entry to `blueprint_actions.yaml`
   - Submit PR for review

2. **For Marketplace Recommendations:**
   - Propose action in issue
   - Get approval from platform team
   - Add to `blueprint_actions.yaml`
   - Submit PR for review

**Process:**
1. Create feature branch
2. Update `blueprint_actions.yaml`
3. Test locally with `generate_website.py`
4. Commit with clear messages
5. Create Pull Request
6. Get team approval
7. Merge and auto-deploy

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or action requests:
- Open an issue on GitHub
- Contact your DevOps/Platform team
- Check existing issues first

## Internal Resources

- [Internal Actions Documentation](https://github.com/your-org)
- [Workflow Examples](https://github.com/your-org)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## FAQ

**Q: Can I use actions from this catalog in my workflows?**
A: Yes! This catalog is designed for your organization to discover and use both internal and approved marketplace actions.

**Q: Who maintains this catalog?**
A: Your organization's DevOps/Platform team manages and curates the action list.

**Q: How do I request a new internal action?**
A: Open an issue or contact your platform team with your use case.

**Q: Can I use marketplace actions not in this catalog?**
A: Check with your platform team about your organization's action policies.

**Q: How often is the catalog updated?**
A: Automatically when changes are committed. Check the workflow runs for status.

---

**Last Updated:** December 2024

**Total Actions:** 344+

**Internal Actions:** 45+

**Marketplace Actions:** 299+

**Categories:** 8 primary categories

Made by your organization for your organization 🚀
