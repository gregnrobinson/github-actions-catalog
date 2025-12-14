#!/usr/bin/env python3
"""
Local web frontend to visualize and navigate the action catalog.
Provides search, filtering by category, and action details.
"""

import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
CATALOG_DIR = Path.cwd() / "catalog"

def get_all_actions():
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

def get_categories():
    """Get all unique categories from catalog."""
    categories = set()

    for action in get_all_actions():
        for cat in action.get("annotations", {}).get("categories", []):
            categories.add(cat)

    return sorted(list(categories))

@app.route("/")
def index():
    """Main catalog page."""
    actions = get_all_actions()
    categories = get_categories()

    return render_template("index.html",
                         total_actions=len(actions),
                         categories=categories)

@app.route("/api/actions")
def api_actions():
    """API endpoint to get filtered actions."""
    search_query = request.args.get("search", "").lower()
    category_filter = request.args.get("category", "")

    actions = get_all_actions()
    filtered = []

    for action in actions:
        # Category filter
        if category_filter:
            if category_filter not in action.get("annotations", {}).get("categories", []):
                continue

        # Search filter
        if search_query:
            action_id = action.get("action_id", "").lower()
            name = action.get("definition", {}).get("name", "").lower()
            description = action.get("definition", {}).get("description", "").lower()

            if not (search_query in action_id or
                   search_query in name or
                   search_query in description):
                continue

        # Add to results
        filtered.append({
            "action_id": action.get("action_id"),
            "name": action.get("definition", {}).get("name", ""),
            "description": action.get("definition", {}).get("description", ""),
            "categories": action.get("annotations", {}).get("categories", []),
            "confidence": action.get("annotations", {}).get("confidence", ""),
            "author": action.get("definition", {}).get("author", ""),
            "source_type": action.get("source", {}).get("type", ""),
            "publisher": action.get("source", {}).get("publisher"),
            "verified": action.get("source", {}).get("verified", False)
        })

    return jsonify(filtered)

@app.route("/api/actions/<path:action_id>")
def api_action_detail(action_id):
    """API endpoint to get full action details."""
    # Sanitize action_id for filesystem
    sanitized_id = action_id.replace("/", "__")

    entry_dir = CATALOG_DIR / sanitized_id
    latest_file = entry_dir / "latest.json"

    if not latest_file.exists():
        return jsonify({"error": "Action not found"}), 404

    with open(latest_file, "r") as f:
        action = json.load(f)

    return jsonify(action)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
