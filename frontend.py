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

def get_action_type(action):
    """Determine if action is marketplace or internal."""
    source = action.get("source", {})

    # Check source.type field first (most reliable)
    if source.get("type") == "marketplace":
        return "marketplace"
    elif source.get("type") == "internal":
        return "internal"

    # Fallback: check action_id or publisher
    action_id = action.get("action_id", "").lower()
    if action_id.startswith("marketplace/"):
        return "marketplace"

    return "internal"

def get_catalog_stats():
    """Get catalog statistics."""
    actions = get_all_actions()

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

@app.route("/")
def index():
    """Main catalog page."""
    actions = get_all_actions()
    categories = get_categories()
    stats = get_catalog_stats()

    return render_template("index.html",
                         total_actions=stats["total"],
                         internal_actions=stats["internal"],
                         marketplace_actions=stats["marketplace"],
                         verified_actions=stats["verified"],
                         categories=categories)

@app.route("/api/actions")
def api_actions():
    """API endpoint to get filtered actions."""
    search_query = request.args.get("search", "").lower()
    category_filter = request.args.get("category", "")
    action_type = request.args.get("type", "")  # "internal", "marketplace", or ""

    actions = get_all_actions()
    filtered = []

    for action in actions:
        # Type filter (internal vs marketplace)
        if action_type:
            detected_type = get_action_type(action)
            if action_type != detected_type:
                continue

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

        # Determine action type
        detected_type = get_action_type(action)

        # Add to results
        filtered.append({
            "action_id": action.get("action_id"),
            "name": action.get("definition", {}).get("name", ""),
            "description": action.get("definition", {}).get("description", ""),
            "categories": action.get("annotations", {}).get("categories", []),
            "confidence": action.get("annotations", {}).get("confidence", ""),
            "author": action.get("definition", {}).get("author", ""),
            "publisher": action.get("source", {}).get("publisher"),
            "verified": action.get("source", {}).get("verified", False),
            "origin": action.get("source", {}).get("origin", ""),
            "type": detected_type
        })

    return jsonify(filtered)

@app.route("/api/actions/<path:action_id>")
def api_action_detail(action_id):
    """API endpoint to get full action details."""
    # Handle both regular and sanitized action IDs
    original_id = action_id.replace("__", "/")
    sanitized_id = action_id.replace("/", "__")

    # Try to find the action directory
    entry_dir = None
    for potential_dir in [CATALOG_DIR / sanitized_id, CATALOG_DIR / original_id]:
        if potential_dir.exists():
            entry_dir = potential_dir
            break

    if not entry_dir:
        return jsonify({"error": "Action not found"}), 404

    latest_file = entry_dir / "latest.json"

    if not latest_file.exists():
        return jsonify({"error": "Action not found"}), 404

    with open(latest_file, "r") as f:
        action = json.load(f)

    # Determine action type
    detected_type = get_action_type(action)
    action["type"] = detected_type

    return jsonify(action)

@app.route("/api/stats")
def api_stats():
    """API endpoint to get catalog statistics."""
    stats = get_catalog_stats()
    categories = get_categories()

    return jsonify({
        "total_actions": stats["total"],
        "internal_actions": stats["internal"],
        "marketplace_actions": stats["marketplace"],
        "verified_actions": stats["verified"],
        "categories": categories
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
