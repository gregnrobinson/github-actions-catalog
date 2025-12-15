# 🚀 GitHub Actions Catalog

A fully static, self-hosted catalog platform for organizations to discover and manage both official internal actions and curated marketplace actions. **100% hosted on GitHub Pages** - no external infrastructure required.

## 🌐 Live Demo

**[View Live Demo →](https://gregnrobinson.github.io/github-actions-catalog)**

Try the catalog now! Search, filter, and explore actions with the workflow builder.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- **GitHub Personal Access Token** (for fetching release information)
- **OpenAI API Key** (optional, for AI-powered action categorization)

### Installation

```bash
git clone https://github.com/gregnrobinson/github-actions-catalog.git
cd github-actions-catalog
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file or export these variables:

```bash
# Required for fetching GitHub release information
export GITHUB_TOKEN="ghp_your_github_token_here" # pragma: allowlist secret

# Optional: Required only if using AI categorization
export OPENAI_API_KEY="sk-your_openai_api_key_here" # pragma: allowlist secret
```

**Getting Tokens:**

1. **GitHub Token**: Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) and create a token with `public_repo` scope
2. **OpenAI API Key** (optional): Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### Build Everything

```bash
# Build catalog and generate website in one command
./build.sh
```

Or run individual scripts:

```bash
# Build catalog without AI categorization (no OpenAI key needed)
python3 build_catalog.py --no-categorize

# Build catalog with AI categorization (requires OpenAI key)
python3 build_catalog.py

# Generate static website
python3 generate_website.py

# Test locally
cd docs
python3 -m http.server 8000
```

Visit `http://localhost:8000` in your browser.

---

## What's Included

### 🔍 Features

- **Action Catalog** - Browse internal and marketplace actions
- **Smart Search** - Filter by name, category, or description
- **Workflow Builder** - Visual workflow generator with YAML output
- **Action Details** - View inputs, outputs, and usage examples
- **Publisher Verification** - Distinguish internal vs marketplace actions
- **AI Categorization** - Automatic action categorization with OpenAI (optional)
- **Zero Infrastructure** - 100% static site hosted on GitHub Pages

### 🏗️ Architecture

This catalog is completely serverless and runs entirely on GitHub Pages:

- **Static HTML/CSS/JS** - No backend server required
- **GitHub Pages Hosting** - Free, reliable, and scalable
- **Build-time Generation** - Catalog built once, served as static files
- **Client-side Search** - Fast filtering without server calls
- **Zero Cost** - No hosting fees, only GitHub Pages (free for public repos)

### 📁 Project Structure

```
github-actions-catalog/
├── blueprints/
│   ├── internal_actions/              # Your custom actions
│   │   └── your-org/
│   │       └── deploy-action/
│   │           └── action.yml
│   └── marketplace_actions/           # Curated marketplace actions
│       └── actions/
│           └── checkout/
│               └── action.yml
├── config/
│   └── categorization_config.yaml     # Category mappings
├── catalog/                            # Generated catalog data
│   └── catalog.json
├── docs/                               # Generated website (GitHub Pages source)
│   ├── index.html                     # Main catalog page
│   ├── workflow-builder.html          # Workflow builder
│   └── styles.css                     # Styling
├── build_catalog.py                   # Catalog builder
├── generate_website.py                # Website generator
├── requirements.txt                   # Python dependencies
└── build.sh                           # Build everything
```

---

## Adding Actions

### 1. Create Action in Blueprints

Add your action under `blueprints/internal_actions/`:

```bash
# Create action directory
mkdir -p blueprints/internal_actions/your-org/deploy-action

# Create action.yml
cat > blueprints/internal_actions/your-org/deploy-action/action.yml << 'EOF'
name: "Deploy to Production"
description: "Deploy applications to production environment"
author: "Platform Team"

inputs:
  environment:
    description: "Target environment"
    required: true
  version:
    description: "Application version to deploy"
    required: false
    default: "latest"

outputs:
  deployment-url:
    description: "Deployed application URL"

runs:
  using: "composite"
  steps:
    - name: Deploy
      shell: bash
      run: |
        echo "Deploying to ${{ inputs.environment }}"
EOF
```

### 2. Rebuild

```bash
./build.sh
```

### 3. Deploy

```bash
git add .
git commit -m "Add deploy action"
git push
```

The GitHub Actions workflow will automatically deploy to GitHub Pages.

---

## Configuration

### GitHub Pages Setup

1. Go to repository **Settings** → **Pages**
2. Set source to **Deploy from a branch**
3. Select branch: **main**, folder: **/docs**
4. Click **Save**

Your catalog will be live at: `https://<username>.github.io/<repo>/`

**That's it!** No servers, no infrastructure, no deployment pipelines. GitHub Pages automatically serves your static site.

### Automation

The `.github/workflows/generate-pages.yml` workflow automatically:
- Rebuilds catalog when actions change
- Regenerates static website files
- Commits updated files to `docs/` folder
- GitHub Pages automatically deploys the changes

**Requirements:**
- Personal Access Token (PAT) with `repo` scope
- Stored as `CATALOG_DEPLOY_TOKEN` in repository secrets

**How it works:**
1. Push changes to blueprints or config
2. GitHub Actions runs build scripts
3. Commits generated files to `docs/`
4. GitHub Pages serves updated site (usually within 1-2 minutes)

---

## Development

### Build Options

```bash
# Build catalog without AI categorization (faster, no OpenAI key needed)
python3 build_catalog.py --no-categorize

# Build with AI categorization
python3 build_catalog.py

# Force rebuild all actions (ignore cache)
python3 build_catalog.py --no-cache

# Force re-categorize all actions
python3 build_catalog.py --force-categorize

# Update only release information
python3 build_catalog.py --update-releases

# Update publisher verification status
python3 build_catalog.py --force-publisher-update
```

### Generate Website Only

```bash
python3 generate_website.py
```

### Test Locally

```bash
cd docs
python3 -m http.server 8000
```

Open `http://localhost:8000` - you'll see exactly what GitHub Pages will serve.

### Cost Management

The catalog builder can use OpenAI GPT-4o-mini for automatic categorization:
- **Cost**: ~$0.0001-0.0003 per action
- **Total**: ~$0.03-0.10 for 300+ actions
- **Caching**: Only categorizes new/changed actions

Skip categorization to avoid costs:
```bash
python3 build_catalog.py --no-categorize
```

**GitHub Pages is free for:**
- Public repositories (unlimited)
- Private repositories (limited bandwidth)

---

## Why GitHub Pages?

✅ **Zero Infrastructure** - No servers to maintain.<br>
✅ **Zero Cost** - Free for public repos.<br>
✅ **Global CDN** - Fast worldwide access.<br>
✅ **Auto SSL** - HTTPS by default.<br>
✅ **Git-based Deployment** - Just commit and push.<br>
✅ **High Availability** - Backed by GitHub's infrastructure.<br>
✅ **Version Control** - Every change is tracked in git.<br>

---

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/gregnrobinson/github-actions-catalog/issues)
- Check [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Check [GitHub Pages Documentation](https://docs.github.com/en/pages)
- Contact your DevOps/Platform team
