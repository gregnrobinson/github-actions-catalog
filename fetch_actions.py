#!/usr/bin/env python3
"""
Fetch GitHub marketplace actions from approved publishers using GraphQL.
Reads approved publishers from config/publishers.json
Populates blueprints/marketplace/ with action.yml files.
"""

import os
import json
import requests
from pathlib import Path

GITHUB_API_BASE = "https://api.github.com/graphql"
BLUEPRINTS_DIR = Path.cwd() / "blueprints"
MARKETPLACE_DIR = BLUEPRINTS_DIR / "marketplace"
CONFIG_DIR = Path.cwd() / "config"
APPROVED_PUBLISHERS_FILE = CONFIG_DIR / "publishers.json"

# Create directories
MARKETPLACE_DIR.mkdir(parents=True, exist_ok=True)

def get_github_token():
    """Get GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required for GraphQL queries")
    return token

def load_approved_publishers():
    """Load approved publishers list from JSON file."""
    if not APPROVED_PUBLISHERS_FILE.exists():
        print(f"❌ {APPROVED_PUBLISHERS_FILE} not found")
        print("   Run: python3 scripts/fetch_approved_publishers.py first\n")
        return []

    with open(APPROVED_PUBLISHERS_FILE, "r") as f:
        data = json.load(f)

    publishers = []

    # Handle new structure: publishers is a list of objects with 'name' field
    if isinstance(data.get("publishers"), list):
        for pub in data["publishers"]:
            if isinstance(pub, dict) and "name" in pub:
                publishers.append(pub["name"])
            elif isinstance(pub, str):
                publishers.append(pub)

    return publishers

def graphql_query(query, variables=None):
    """Execute a GraphQL query."""
    token = get_github_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "variables": variables or {}
    }

    response = requests.post(GITHUB_API_BASE, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"GraphQL Error: {response.status_code}")
        return None

    data = response.json()

    if "errors" in data:
        print(f"GraphQL Errors: {data['errors']}")
        return None

    return data.get("data")

def fetch_publisher_actions(publisher):
    """Fetch all repos with action.yml files from a publisher using GraphQL."""

    query = """
    query($owner: String!, $after: String) {
      repositoryOwner(login: $owner) {
        repositories(first: 100, after: $after, privacy: PUBLIC, orderBy: {field: STARGAZERS, direction: DESC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            name
            description
            url
            stargazerCount
            primaryLanguage {
              name
            }
            action: object(expression: "HEAD:action.yml") {
              ... on Blob {
                text
              }
            }
            actionYaml: object(expression: "HEAD:action.yaml") {
              ... on Blob {
                text
              }
            }
          }
        }
      }
    }
    """

    actions = []
    after_cursor = None

    while True:
        variables = {"owner": publisher, "after": after_cursor}
        result = graphql_query(query, variables)

        if not result or "repositoryOwner" not in result:
            break

        owner = result["repositoryOwner"]
        if not owner or "repositories" not in owner:
            break

        repos = owner["repositories"]

        for repo in repos["nodes"]:
            # Check if repo has action.yml or action.yaml
            action_content = repo.get("action", {})
            if not action_content and repo.get("actionYaml"):
                action_content = repo.get("actionYaml", {})

            if action_content and action_content.get("text"):
                actions.append({
                    "name": repo["name"],
                    "description": repo["description"],
                    "url": repo["url"],
                    "stars": repo["stargazerCount"],
                    "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
                    "action_yml": action_content["text"]
                })

        # Check for pagination
        if not repos["pageInfo"]["hasNextPage"]:
            break

        after_cursor = repos["pageInfo"]["endCursor"]

    return actions

def save_action_yml(publisher, action_name, action_yml_content):
    """Save action.yml to marketplace folder."""
    # Create folder: blueprints/marketplace/{publisher}/{action_name}
    action_dir = MARKETPLACE_DIR / publisher / action_name
    action_dir.mkdir(parents=True, exist_ok=True)

    # Write action.yml
    action_file = action_dir / "action.yml"
    action_file.write_text(action_yml_content)

    return action_dir

def main():
    """Main fetch workflow."""
    print("📦 Fetching GitHub Actions from approved publishers\n")

    publishers = load_approved_publishers()

    if not publishers:
        return

    print(f"Found {len(publishers)} approved publishers\n")

    total_success = 0
    total_failed = 0

    for publisher in publishers:
        print(f"📍 {publisher}")

        # Fetch actions from publisher
        actions = fetch_publisher_actions(publisher)

        if not actions:
            print(f"  No actions found")
            print()
            continue

        print(f"  Found {len(actions)} action(s)")

        for action in actions:
            action_name = action['name']
            print(f"    {publisher}/{action_name}...", end=" ")
            try:
                save_action_yml(publisher, action_name, action["action_yml"])
                print("✅")
                total_success += 1
            except Exception as e:
                print(f"❌ ({e})")
                total_failed += 1

        print()

    print(f"✅ Fetched: {total_success} actions")
    if total_failed > 0:
        print(f"❌ Failed: {total_failed} actions")
    print(f"📁 Output: {MARKETPLACE_DIR.relative_to(Path.cwd())}")

if __name__ == "__main__":
    main()
