#!/usr/bin/env python3
"""
Imports and PUBLISHES the updated n8n workflow using official n8n CLI commands.
This ensures:
1. workflow_entity is updated.
2. workflow_history gets the new version snapshot.
3. workflow_published_version is set to the new version ID.
4. Active webhooks and production execution graph are re-registered.
"""
import json
import subprocess
import os

BLUEPRINT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "n8n_workflow_blueprint.json")

def main():
    print("Loading blueprint from:", BLUEPRINT_PATH)
    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    # Format as n8n workflow array with ID and active: true
    workflow_obj = {
        "id": "SDAJiNePGG1J3TzW",
        "name": blueprint.get("name", "nuDesk Operations Studio - Multi-Flow Triage & Google Workspace Sync"),
        "active": True,
        "nodes": blueprint.get("nodes", []),
        "connections": blueprint.get("connections", {}),
        "settings": blueprint.get("settings", {"executionOrder": "v1"})
    }

    import_array = [workflow_obj]
    tmp_local = "/tmp/n8n_import_payload.json"
    with open(tmp_local, "w", encoding="utf-8") as f:
        json.dump(import_array, f, indent=2)

    print("Copying import payload to Docker container...")
    subprocess.run(["docker", "cp", tmp_local, "nudesk_n8n:/tmp/n8n_import_payload.json"], check=True)

    print("Running: n8n import:workflow...")
    res_import = subprocess.run(
        ["docker", "exec", "nudesk_n8n", "n8n", "import:workflow", "--input=/tmp/n8n_import_payload.json", "--activeState=fromJson"],
        capture_output=True, text=True
    )
    print("IMPORT STDOUT:", res_import.stdout)
    if res_import.stderr:
        print("IMPORT STDERR:", res_import.stderr)

    print("Running: n8n publish:workflow --id=SDAJiNePGG1J3TzW...")
    res_publish = subprocess.run(
        ["docker", "exec", "nudesk_n8n", "n8n", "publish:workflow", "--id=SDAJiNePGG1J3TzW"],
        capture_output=True, text=True
    )
    print("PUBLISH STDOUT:", res_publish.stdout)
    if res_publish.stderr:
        print("PUBLISH STDERR:", res_publish.stderr)

    print("Restarting n8n container to reload memory cache...")
    subprocess.run(["docker", "restart", "nudesk_n8n"], check=True)
    print("Done! Workflow published and reloaded.")

if __name__ == "__main__":
    main()
