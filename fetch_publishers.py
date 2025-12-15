#!/usr/bin/env python3
"""
Fetch approved/verified GitHub Action publishers from GitHub Marketplace.
Stores publisher list in publishers.json for later use.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime

GITHUB_API_BASE = "https://api.github.com/graphql"
CONFIG_DIR = Path.cwd() / "config"
APPROVED_PUBLISHERS_FILE = CONFIG_DIR / "publishers.json"

# Create config directory if it doesn't exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Official organizations to always include
OFFICIAL_ORGS = [
    "actions",
    "azure",
    "aws-actions",
    "google-github-actions",
    "docker",
    "codecov",
    "github"
]

def get_github_token():
    """Get GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return token

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

def search_github_actions(query, min_stars=100):
    """Search for GitHub Actions using GraphQL."""

    graphql_query_str = """
    query($searchQuery: String!, $after: String) {
      search(query: $searchQuery, type: REPOSITORY, first: 100, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            id
            name
            owner {
              login
            }
            stargazerCount
          }
        }
      }
    }
    """

    repos = []
    after_cursor = None

    while True:
        search_query = f"{query} topic:github-action stars:>{min_stars}"
        variables = {
            "searchQuery": search_query,
            "after": after_cursor
        }

        result = graphql_query(graphql_query_str, variables)

        if not result or "search" not in result:
            break

        search_results = result["search"]
        nodes = search_results.get("nodes", [])

        if not nodes:
            break

        for node in nodes:
            repos.append({
                "id": node["id"],
                "name": node["name"],
                "owner": {"login": node["owner"]["login"]},
                "stargazerCount": node["stargazerCount"]
            })

        print(f"    Page: Found {len(nodes)} results")

        # Check for pagination
        if not search_results["pageInfo"]["hasNextPage"]:
            break

        after_cursor = search_results["pageInfo"]["endCursor"]

    return repos

def save_approved_publishers(publishers_list):
    """Save approved publishers list to JSON file."""
    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_publishers": len(publishers_list),
            "verified_count": sum(1 for p in publishers_list if p.get("verified")),
            "community_count": sum(1 for p in publishers_list if not p.get("verified")),
            "source": "GitHub Marketplace API",
            "version": "2.0"
        },
        "publishers": publishers_list
    }

    with open(APPROVED_PUBLISHERS_FILE, "w") as f:
        json.dump(output, f, indent=2)

def main():
    """Main workflow."""
    print("🔍 Fetching approved GitHub Action publishers (using GraphQL)\n")

    # Start with verified creators
    print("📌 Adding official verified creators:")
    publishers_list = []

    for org in OFFICIAL_ORGS:
        publishers_list.append({
            "name": org,
            "verified": True,
            "type": "official"
        })
        print(f"  ✓ {org}")

    # Search for popular community actions
    print("\n🔎 Searching for popular community action publishers (100+ stars)...\n")

    search_queries = [
        "github-action",
        "workflow",
        "ci-cd",
        "action",
        "github-actions",
        "automation",
        "devops"
    ]

    all_repos = []
    for query in search_queries:
        print(f"  Searching: {query}...")
        repos = search_github_actions(query, min_stars=100)
        all_repos.extend(repos)
        print(f"    Total found: {len(repos)} repositories\n")

    # Remove duplicates
    seen = set()
    unique_repos = []
    for repo in all_repos:
        if repo["id"] not in seen:
            seen.add(repo["id"])
            unique_repos.append(repo)

    print(f"✅ Total unique repositories: {len(unique_repos)}\n")

    # Extract publishers from community actions
    community_publishers = set()
    for repo in unique_repos:
        community_publishers.add(repo["owner"]["login"])

    # Add community publishers to list
    for publisher in sorted(community_publishers):
        if publisher not in [p["name"] for p in publishers_list]:
            publishers_list.append({
                "name": publisher,
                "verified": False,
                "type": "community",
                "stars": next((repo["stargazerCount"] for repo in unique_repos if repo["owner"]["login"] == publisher), 0)
            })

    # Save to file
    save_approved_publishers(publishers_list)

    verified_count = sum(1 for p in publishers_list if p.get("verified"))
    community_count = len(publishers_list) - verified_count

    print(f"✅ Saved {len(publishers_list)} approved publishers")
    print(f"   - {verified_count} verified (official)")
    print(f"   - {community_count} community\n")
    print(f"📁 File: {APPROVED_PUBLISHERS_FILE.relative_to(Path.cwd())}\n")

    print("📊 Verified Publishers:")
    verified = [p for p in publishers_list if p.get("verified")]
    for i, publisher in enumerate(verified, 1):
        print(f"  {i:2d}. ✓ {publisher['name']}")

    print(f"\n📊 Community Publishers (Sample - 100+ stars):")
    community = [p for p in publishers_list if not p.get("verified")]
    for i, publisher in enumerate(community[:20], 1):
        stars = publisher.get("stars", 0)
        print(f"  {i:2d}.   {publisher['name']:40s} ⭐ {stars}")

    if len(community) > 20:
        print(f"  ... and {len(community) - 20} more")

if __name__ == "__main__":
    main()
