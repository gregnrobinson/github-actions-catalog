#!/usr/bin/env python3
"""
Fetch GitHub marketplace actions from approved publishers using GraphQL.
Reads approved publishers from config/approved_publishers.json
Populates blueprints/marketplace/ with action.yml files.
"""

import os
import json
import requests
from pathlib import Path

GITHUB_API_BASE = "https://api.github.com/graphql"
REST_API_BASE = "https://api.github.com"
BLUEPRINTS_DIR = Path.cwd() / "blueprints"
MARKETPLACE_DIR = BLUEPRINTS_DIR / "marketplace"
CONFIG_DIR = Path.cwd() / "config"
APPROVED_PUBLISHERS_FILE = CONFIG_DIR / "approved_publishers.json"

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

    return data.get("publishers", [])

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

def fetch_publisher_repos_with_actions(publisher):
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

    repos_with_actions = []
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
                repos_with_actions.append({
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

    return repos_with_actions

def fetch_composite_actions(publisher):
    """Fetch composite actions from .github/actions/ directories using GraphQL."""

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
            githubDir: object(expression: "HEAD:.github/actions") {
              ... on Tree {
                entries {
                  name
                  type
                  object {
                    ... on Blob {
                      text
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    composite_actions = []
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
            github_dir = repo.get("githubDir")
            if not github_dir:
                continue

            # Fetch each action in .github/actions/
            for entry in github_dir.get("entries", []):
                if entry["type"] == "Tree":  # It's a directory
                    action_name = entry["name"]
                    # We need to fetch the action.yml for this action
                    # This requires another API call, so we'll do it via REST
                    action_yml = download_composite_action_yml(publisher, repo["name"], action_name)
                    if action_yml:
                        composite_actions.append({
                            "name": f"{repo['name']}-{action_name}",
                            "description": repo["description"],
                            "url": f"{repo['url']}/tree/HEAD/.github/actions/{action_name}",
                            "stars": repo["stargazerCount"],
                            "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
                            "action_yml": action_yml,
                            "is_composite": True
                        })

        # Check for pagination
        if not repos["pageInfo"]["hasNextPage"]:
            break

        after_cursor = repos["pageInfo"]["endCursor"]

    return composite_actions

def download_composite_action_yml(publisher, repo_name, action_name):
    """Download action.yml for a composite action via REST API."""
    token = get_github_token()
    headers = {"Authorization": f"token {token}"}

    url = f"{REST_API_BASE}/repos/{publisher}/{repo_name}/contents/.github/actions/{action_name}/action.yml"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = response.json()
        if content.get("type") == "file":
            import base64
            return base64.b64decode(content["content"]).decode("utf-8")

    # Try action.yaml
    url = f"{REST_API_BASE}/repos/{publisher}/{repo_name}/contents/.github/actions/{action_name}/action.yaml"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = response.json()
        if content.get("type") == "file":
            import base64
            return base64.b64decode(content["content"]).decode("utf-8")

    return None

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
    print("📦 Fetching GitHub Actions from approved publishers (using GraphQL)\n")

    publishers = load_approved_publishers()

    if not publishers:
        return

    print(f"Found {len(publishers)} approved publishers\n")

    total_success = 0
    total_failed = 0

    for publisher in publishers:
        print(f"📍 {publisher}")

        # Fetch root-level actions
        print(f"  Fetching root-level actions...")
        root_actions = fetch_publisher_repos_with_actions(publisher)

        for action in root_actions:
            action_name = action['name']
            print(f"    {publisher}/{action_name}...", end=" ")
            try:
                save_action_yml(publisher, action_name, action["action_yml"])
                print("✅")
                total_success += 1
            except Exception as e:
                print(f"❌ ({e})")
                total_failed += 1

        # Fetch composite actions
        print(f"  Fetching composite actions...")
        composite_actions = fetch_composite_actions(publisher)

        for action in composite_actions:
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
    print(f"❌ Failed: {total_failed} actions")
    print(f"📁 Output: {MARKETPLACE_DIR.relative_to(Path.cwd())}")

if __name__ == "__main__":
    main()
