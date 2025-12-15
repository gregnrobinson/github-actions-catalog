#!/bin/bash
# filepath: /Users/gregrobinson/repos/github-actions-catalog/sync.sh

set -e  # Exit on error

echo "🚀 Starting full sync of GitHub Actions Catalog"
echo "================================================"
echo ""

# Install Dependencies
echo "🔧 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Step 1: Fetch publishers
echo "📥 Step 1: Fetching publishers..."
python3 fetch_publishers.py
echo "✅ Publishers fetched"
echo ""

# Step 2: Fetch actions
echo "📥 Step 2: Fetching actions..."
python3 fetch_actions.py
echo "✅ Actions fetched"
echo ""

# Step 3: Build catalog
echo "📦 Step 3: Building catalog..."
python3 build_catalog.py
echo "✅ Catalog built"
echo ""

# Step 4: Generate website
echo "🌐 Step 4: Generating website..."
python3 generate_website.py
echo "✅ Website generated"
echo ""

echo "================================================"
echo "✨ Full sync complete!"
echo ""
echo "📁 Output directories:"
echo "   - blueprints/ (action blueprints)"
echo "   - catalog/ (catalog entries)"
echo "   - docs/ (website)"
