#!/usr/bin/env python3
"""
Build action catalog from internal and marketplace actions.
Scans action.yml files and generates latest.json + versioned snapshots.
Then categorizes actions using OpenAI GPT with cost tracking.
Includes caching to skip unchanged files (use --no-cache to force rebuild).
Fetches latest GitHub releases for marketplace actions.
"""

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml
from openai import OpenAI

# Use current working directory
BLUEPRINTS_DIR = Path.cwd() / "blueprints"
CATALOG_DIR = Path.cwd() / "catalog"

# GitHub API token from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# GitHub Marketplace action categories
GITHUB_CATEGORIES = [
    "Authentication",
    "Build",
    "Communication",
    "Code quality",
    "Deployment",
    "Dependency management",
    "Documentation",
    "Infrastructure",
    "Monitoring",
    "Notification",
    "Packaging",
    "Publishing",
    "Security",
    "Testing"
]

# Create catalog directory if it doesn't exist
CATALOG_DIR.mkdir(parents=True, exist_ok=True)

# Parse command line flags
USE_CACHE = "--no-cache" not in sys.argv
SKIP_CATEGORIZE = "--no-categorize" in sys.argv
FORCE_CATEGORIZE = "--force-categorize" in sys.argv
FORCE_PUBLISHER_UPDATE = "--force-publisher-update" in sys.argv
UPDATE_RELEASES = "--update-releases" in sys.argv

def get_latest_release(origin):
    """Fetch latest release from GitHub repository."""
    if not origin or not GITHUB_TOKEN:
        return None

    try:
        import requests

        # Extract owner/repo from origin (e.g., github.com/actions/checkout)
        parts = origin.replace("github.com/", "").split("/")
        if len(parts) < 2:
            return None

        owner = parts[0]
        repo = parts[1]

        # GitHub API endpoint for latest release
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            release_data = response.json()
            return {
                "tag_name": release_data.get("tag_name"),
                "name": release_data.get("name"),
                "published_at": release_data.get("published_at"),
                "html_url": release_data.get("html_url"),
                "prerelease": release_data.get("prerelease", False),
                "draft": release_data.get("draft", False)
            }
        elif response.status_code == 404:
            # No releases found
            return None
        else:
            return None

    except Exception:
        return None

def update_release_info_only():
    """Update only release information in existing catalog entries."""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set - cannot fetch releases")
        return

    print("🔄 Updating release information for marketplace actions\n")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    # Find all catalog entries
    if not CATALOG_DIR.exists():
        print("❌ Catalog directory not found")
        return

    for entry_dir in CATALOG_DIR.iterdir():
        if not entry_dir.is_dir():
            continue

        latest_file = entry_dir / "latest.json"
        if not latest_file.exists():
            continue

        try:
            # Load existing entry
            with open(latest_file, "r") as f:
                catalog_entry = json.load(f)

            action_id = catalog_entry.get("action_id", "")
            source = catalog_entry.get("source", {})
            origin = source.get("origin")

            # Only update marketplace actions with origin
            if source.get("type") != "marketplace" or not origin:
                continue

            print(f"Updating {action_id}...", end=" ", flush=True)

            # Fetch latest release
            latest_release = get_latest_release(origin)

            if latest_release:
                # Update release info
                old_release = source.get("latest_release", {})
                old_tag = old_release.get("tag_name", "none")
                new_tag = latest_release.get("tag_name", "unknown")

                source["latest_release"] = latest_release
                catalog_entry["source"] = source

                # Save updated entry
                with open(latest_file, "w") as f:
                    json.dump(catalog_entry, f, indent=2)

                # Also update versioned file if it exists
                version_id = catalog_entry.get("version_id")
                if version_id:
                    version_file = entry_dir / f"{version_id}.json"
                    if version_file.exists():
                        with open(version_file, "w") as f:
                            json.dump(catalog_entry, f, indent=2)

                if old_tag != new_tag:
                    print(f"✅ Updated {old_tag} → {new_tag}")
                else:
                    print(f"✅ {new_tag} (unchanged)")
                updated_count += 1
            else:
                print("⏭️  No release found")
                skipped_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            error_count += 1

    print(f"\n✅ Updated: {updated_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")

def load_approved_publishers():
    """Load approved publishers from config file."""
    config_file = Path.cwd() / "config" / "publishers.json"

    if not config_file.exists():
        return {}

    try:
        with open(config_file, "r") as f:
            data = json.load(f)

        # Convert list of publisher objects to dict for easy lookup
        publishers_dict = {}
        for pub in data.get("publishers", []):
            publishers_dict[pub["name"]] = pub.get("verified", False)

        return publishers_dict
    except Exception as e:
        print(f"Warning: Could not load approved publishers: {e}")
        return {}

# Load approved publishers at startup
APPROVED_PUBLISHERS = load_approved_publishers()

def compute_version_id(action_yml_bytes):
    """Compute version_id as first 12 chars of SHA256."""
    sha256_hash = hashlib.sha256(action_yml_bytes).hexdigest()
    return sha256_hash[:12]

def parse_action_yml(action_yml_path):
    """Parse action.yml and extract definition."""
    try:
        with open(action_yml_path, "r") as f:
            content = f.read()
        data = yaml.safe_load(content)
        return data, content.encode("utf-8")
    except Exception as e:
        print(f"  ⚠️  Failed to parse {action_yml_path}: {e}")
        return None, None

def sanitize_id(action_id):
    """Sanitize action_id for filesystem path (/ -> __)."""
    return action_id.replace("/", "__")

def get_existing_catalog_hash(action_id):
    """Get the source hash of an existing catalog entry."""
    sanitized_id = sanitize_id(action_id)
    entry_dir = CATALOG_DIR / sanitized_id
    latest_file = entry_dir / "latest.json"

    if not latest_file.exists():
        return None

    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
        return data.get("cache", {}).get("source_hash")
    except Exception:
        return None

def get_existing_publisher_verified(action_id):
    """Get the verified status of publisher from existing catalog entry."""
    sanitized_id = sanitize_id(action_id)
    entry_dir = CATALOG_DIR / sanitized_id
    latest_file = entry_dir / "latest.json"

    if not latest_file.exists():
        return None

    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
        return data.get("source", {}).get("verified")
    except Exception:
        return None

def publisher_verification_changed(action_id):
    """Check if publisher verification status has changed."""
    # Extract publisher from action_id (marketplace/{publisher}/{action_name})
    parts = action_id.split("/")
    if len(parts) < 2 or parts[0] != "marketplace":
        return False

    publisher = parts[1]
    current_verified = APPROVED_PUBLISHERS.get(publisher, False)
    existing_verified = get_existing_publisher_verified(action_id)

    return current_verified != existing_verified

def should_rebuild_entry(action_yml_bytes, action_id):
    """Check if entry needs rebuilding based on source hash or publisher status."""
    if not USE_CACHE:
        return True

    if FORCE_PUBLISHER_UPDATE and publisher_verification_changed(action_id):
        return True

    new_hash = hashlib.sha256(action_yml_bytes).hexdigest()
    existing_hash = get_existing_catalog_hash(action_id)
    return new_hash != existing_hash

def find_internal_actions():
    """Find all internal action.yml files."""
    actions = []

    if not BLUEPRINTS_DIR.exists():
        print(f"⚠️  {BLUEPRINTS_DIR} not found")
        return actions

    # Scan: blueprints/*/.github/actions/*/action.yml
    for repo_dir in BLUEPRINTS_DIR.iterdir():
        if not repo_dir.is_dir():
            continue
        if repo_dir.name in ["marketplace", "marketplace_actions"]:
            continue

        actions_dir = repo_dir / ".github" / "actions"
        if not actions_dir.exists():
            continue

        for action_dir in actions_dir.iterdir():
            if not action_dir.is_dir():
                continue

            action_yml = action_dir / "action.yml"
            if action_yml.exists():
                action_id = f"internal/{repo_dir.name}/.github/actions/{action_dir.name}"
                actions.append({
                    "action_id": action_id,
                    "action_yml_path": action_yml,
                    "source_type": "internal",
                    "origin": None
                })

    return actions

def find_marketplace_actions():
    """Find all marketplace action.yml files."""
    actions = []

    marketplace_dir = BLUEPRINTS_DIR / "marketplace"
    if not marketplace_dir.exists():
        return actions

    # Scan: blueprints/marketplace/{publisher}/{action_name}/action.yml
    for publisher_dir in marketplace_dir.iterdir():
        if not publisher_dir.is_dir():
            continue

        publisher = publisher_dir.name

        for action_dir in publisher_dir.iterdir():
            if not action_dir.is_dir():
                continue

            action_yml = action_dir / "action.yml"
            if action_yml.exists():
                action_name = action_dir.name
                action_id = f"marketplace/{publisher}/{action_name}"
                actions.append({
                    "action_id": action_id,
                    "action_yml_path": action_yml,
                    "source_type": "marketplace",
                    "origin": f"github.com/{publisher}/{action_name}"
                })

    return actions

def build_catalog_entry(action_info):
    """Build a complete catalog entry (latest.json structure)."""
    action_id = action_info["action_id"]
    action_yml_path = action_info["action_yml_path"]

    # Parse action.yml
    definition, action_yml_bytes = parse_action_yml(action_yml_path)
    if definition is None:
        return None

    # Compute version_id
    version_id = compute_version_id(action_yml_bytes)

    # Compute full source hash
    source_hash = hashlib.sha256(action_yml_bytes).hexdigest()

    # Extract normalized definition
    normalized = {
        "name": definition.get("name", ""),
        "description": definition.get("description", ""),
        "author": definition.get("author", ""),
        "inputs": [],
        "outputs": [],
        "runs": definition.get("runs", {})
    }

    # Process inputs
    inputs = definition.get("inputs", {})
    if isinstance(inputs, dict):
        for input_name, input_data in inputs.items():
            normalized["inputs"].append({
                "name": input_name,
                "required": input_data.get("required", False),
                "default": input_data.get("default"),
                "description": input_data.get("description", "")
            })

    # Process outputs
    outputs = definition.get("outputs", {})
    if isinstance(outputs, dict):
        for output_name, output_data in outputs.items():
            normalized["outputs"].append({
                "name": output_name,
                "description": output_data.get("description", "")
            })

    # Determine if publisher is verified
    publisher = None
    is_verified = False

    if action_info["source_type"] == "marketplace":
        # Extract publisher from action_id (marketplace/{publisher}/{action_name})
        parts = action_id.split("/")
        if len(parts) >= 2:
            publisher = parts[1]
            # Look up in approved publishers dict
            is_verified = APPROVED_PUBLISHERS.get(publisher, False)

    # Build source object
    source = {
        "type": action_info["source_type"],
        "action_yml_path": str(action_yml_path.relative_to(Path.cwd())),
        "origin": action_info["origin"],
        "publisher": publisher,
        "verified": is_verified
    }

    # Fetch latest release for marketplace actions
    if action_info["source_type"] == "marketplace" and action_info["origin"]:
        latest_release = get_latest_release(action_info["origin"])
        if latest_release:
            source["latest_release"] = latest_release

    # Build catalog entry
    catalog_entry = {
        "action_id": action_id,
        "version_id": version_id,
        "source": source,
        "definition": normalized,
        "annotations": {
            "categories": [],
            "confidence": None,
            "evidence": []
        },
        "cache": {
            "source_hash": source_hash,
            "taxonomy_version": "0.0.1",
            "prompt_version": "v1",
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

    return catalog_entry, version_id

def write_catalog_files(catalog_entry, version_id):
    """Write latest.json and versioned snapshot."""
    action_id = catalog_entry["action_id"]
    sanitized_id = sanitize_id(action_id)

    # Create catalog entry directory
    entry_dir = CATALOG_DIR / sanitized_id
    entry_dir.mkdir(parents=True, exist_ok=True)

    # Write latest.json
    latest_file = entry_dir / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(catalog_entry, f, indent=2)

    # Write versioned snapshot
    version_file = entry_dir / f"{version_id}.json"
    with open(version_file, "w") as f:
        json.dump(catalog_entry, f, indent=2)

    return latest_file, version_file

def categorize_with_llm(action_entry):
    """Use OpenAI GPT to categorize a single action with multi-category support."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    action_id = action_entry["action_id"]
    definition = action_entry["definition"]

    # Build action summary
    action_summary = f"""
Action: {action_id}
Name: {definition['name']}
Description: {definition['description']}
Author: {definition['author']}

Inputs ({len(definition['inputs'])} total):
{json.dumps(definition['inputs'][:3], indent=2)}

Outputs ({len(definition['outputs'])} total):
{json.dumps(definition['outputs'], indent=2)}
"""

    # System prompt
    system_prompt = f"""You are an expert at categorizing GitHub Actions.
Categorize actions into one or more of these categories:
{', '.join(GITHUB_CATEGORIES)}

An action can belong to multiple categories. For example:
- "AWS Assume Role" would be both Authentication + Infrastructure
- "Docker Login" would be Authentication + Packaging
- "Send Slack Notification" would be Communication + Notification

Respond in JSON format with:
{{
  "primary_category": "...",
  "secondary_categories": [...],
  "all_categories": [...],
  "confidence": "high|medium|low",
  "reasoning": "...",
  "tags": ["tag1", "tag2", "tag3"]
}}

- primary_category: The most important category
- secondary_categories: Other relevant categories
- all_categories: All categories combined (for discovery)
- confidence: How confident you are in the categorization
- reasoning: 1-2 sentences explaining why
- tags: 3-5 searchable tags

Only respond with valid JSON, no other text."""

    # User prompt
    user_prompt = f"""Categorize this GitHub Action:

{action_summary}

Provide your categorization as JSON only."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.3,
            max_tokens=400
        )

        # Track usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Cost calculation (gpt-4o-mini pricing)
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        total_cost = input_cost + output_cost

        result = json.loads(response.choices[0].message.content)
        return result, total_cost
    except json.JSONDecodeError as e:
        print(f"\nFailed to parse JSON: {e}")
        return None, 0
    except Exception as e:
        print(f"\nAPI Error: {e}")
        return None, 0

def update_catalog_with_annotations(action_entry, categorization):
    """Update catalog entry with categorization."""
    # Use all_categories if provided, otherwise combine primary + secondary
    if "all_categories" in categorization:
        categories = categorization["all_categories"]
    else:
        categories = [categorization["primary_category"]] + categorization.get("secondary_categories", [])

    action_entry["annotations"]["categories"] = categories
    action_entry["annotations"]["confidence"] = categorization["confidence"]

    action_entry["annotations"]["evidence"] = [{
        "type": "llm_categorization",
        "model": "gpt-4o-mini",
        "primary_category": categorization.get("primary_category"),
        "reasoning": categorization["reasoning"],
        "tags": categorization.get("tags", [])
    }]

    return action_entry

def save_updated_catalog(action_entry):
    """Save updated catalog entry."""
    action_id = action_entry["action_id"]
    sanitized_id = sanitize_id(action_id)

    entry_dir = CATALOG_DIR / sanitized_id
    latest_file = entry_dir / "latest.json"

    with open(latest_file, "w") as f:
        json.dump(action_entry, f, indent=2)

def print_usage():
    """Print usage information."""
    print("\nUsage: python3 build_catalog.py [FLAGS]\n")
    print("Flags:")
    print("  --no-cache                Force rebuild all actions (ignore cache)")
    print("  --no-categorize           Skip OpenAI categorization")
    print("  --force-categorize        Re-categorize all actions")
    print("  --force-publisher-update  Rebuild all marketplace actions if publisher")
    print("                            verification status changed")
    print("  --update-releases         Only update release information (fast)\n")
    print("Environment Variables:")
    print("  GITHUB_TOKEN              GitHub personal access token for release fetching")
    print("  OPENAI_API_KEY            OpenAI API key for categorization\n")

def main():
    """Main catalog build and categorization workflow."""

    # If --update-releases flag is set, only update releases and exit
    if UPDATE_RELEASES:
        update_release_info_only()
        return

    print("🔨 Building action catalog\n")
    print(f"📁 Working directory: {Path.cwd()}")

    if not USE_CACHE:
        print("🚫 Cache disabled (--no-cache)")
    else:
        print("✅ Using cache (use --no-cache to force rebuild)")

    if FORCE_PUBLISHER_UPDATE:
        print("🔄 Force publisher update enabled (--force-publisher-update)")

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set - release information will not be fetched")

    print()

    # Find all actions
    internal_actions = find_internal_actions()
    marketplace_actions = find_marketplace_actions()
    all_actions = internal_actions + marketplace_actions

    print(f"Found {len(internal_actions)} internal actions")
    print(f"Found {len(marketplace_actions)} marketplace actions")
    print(f"Total: {len(all_actions)} actions\n")

    # Build catalog
    print("📝 Building catalog entries...\n")
    built_entries = []
    success_count = 0
    skipped_count = 0
    publisher_updated_count = 0
    releases_fetched = 0

    for action_info in all_actions:
        action_id = action_info["action_id"]
        action_yml_path = action_info["action_yml_path"]

        # Parse to get bytes for hash comparison
        definition, action_yml_bytes = parse_action_yml(action_yml_path)
        if definition is None:
            print(f"Processing {action_id}... ❌")
            continue

        # Check if publisher verification changed
        is_publisher_update = False
        if FORCE_PUBLISHER_UPDATE and publisher_verification_changed(action_id):
            is_publisher_update = True

        # Check if we need to rebuild
        if not should_rebuild_entry(action_yml_bytes, action_id):
            print(f"Processing {action_id}... ⏭️  (unchanged)")
            skipped_count += 1

            # Still load the existing entry for categorization
            sanitized_id = sanitize_id(action_id)
            latest_file = CATALOG_DIR / sanitized_id / "latest.json"
            with open(latest_file, "r") as f:
                built_entries.append(json.load(f))
            continue

        # Need to rebuild
        if is_publisher_update:
            print(f"Processing {action_id}...", end=" ")
            print(f"(publisher verification changed)")
            print(f"Processing {action_id}...", end=" ")
        else:
            print(f"Processing {action_id}...", end=" ")

        # Re-parse and build
        result = build_catalog_entry(action_info)
        if result is None:
            print("❌")
            continue

        catalog_entry, version_id = result
        write_catalog_files(catalog_entry, version_id)
        built_entries.append(catalog_entry)

        # Check if release was fetched
        has_release = catalog_entry.get("source", {}).get("latest_release") is not None
        if has_release:
            releases_fetched += 1

        if is_publisher_update:
            old_verified = get_existing_publisher_verified(action_id)
            new_verified = catalog_entry["source"]["verified"]
            publisher = catalog_entry["source"]["publisher"]
            release_indicator = " 📦" if has_release else ""
            print(f"✅ ({version_id}) {publisher}: {old_verified}→{new_verified}{release_indicator}")
            publisher_updated_count += 1
        else:
            release_indicator = " 📦" if has_release else ""
            print(f"✅ ({version_id}){release_indicator}")

        success_count += 1

    print(f"\n✅ Catalog built: {success_count}/{len(all_actions)} new/updated")
    print(f"⏭️  Skipped: {skipped_count} (unchanged)")
    if publisher_updated_count > 0:
        print(f"🔄 Publisher updates: {publisher_updated_count}")
    if releases_fetched > 0:
        print(f"📦 Releases fetched: {releases_fetched}")
    print()

    # Skip categorization if --no-categorize flag
    if SKIP_CATEGORIZE:
        print("⏭️  Skipping categorization (--no-categorize flag)\n")
        print(f"📁 Output: {CATALOG_DIR.relative_to(Path.cwd())}")
        print_usage()
        return

    # Categorize actions
    print("🤖 Categorizing actions with OpenAI GPT\n")
    categorized_count = 0
    total_spent = 0.0

    for i, entry in enumerate(built_entries, 1):
        action_id = entry["action_id"]

        # Check if already categorized (has evidence)
        evidence = entry.get("annotations", {}).get("evidence", [])
        should_categorize = FORCE_CATEGORIZE or not (evidence and len(evidence) > 0)

        if not should_categorize:
            print(f"[{i}/{len(built_entries)}] {action_id}... ⏭️  (already categorized)")
            continue

        print(f"[{i}/{len(built_entries)}] {action_id}...", end=" ", flush=True)

        result = categorize_with_llm(entry)

        if result[0]:  # result is tuple (categorization, cost)
            categorization, cost = result
            total_spent += cost
            updated_entry = update_catalog_with_annotations(entry, categorization)
            save_updated_catalog(updated_entry)

            primary = categorization["primary_category"]
            all_cats = categorization.get("all_categories", [primary])
            confidence = categorization["confidence"]
            cat_display = ", ".join(all_cats[:2])  # Show first 2 categories
            if len(all_cats) > 2:
                cat_display += f" +{len(all_cats)-2}"

            print(f"✅ ({cat_display}, {confidence}) ${cost:.5f}")
            categorized_count += 1
        else:
            print("⏭️  (skipped)")

    print(f"\n✅ Categorized: {categorized_count}/{len(built_entries)} actions")
    print(f"💰 Total cost: ${total_spent:.2f}")
    print(f"📁 Output: {CATALOG_DIR.relative_to(Path.cwd())}")
    print_usage()

if __name__ == "__main__":
    main()
