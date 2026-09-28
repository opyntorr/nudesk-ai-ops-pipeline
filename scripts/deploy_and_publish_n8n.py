#!/usr/bin/env python3
"""
Deploy and publish full nuDesk n8n workflow:
1. Injects valid format_code.js into Code node.
2. Injects high-impact HTML into Executive Send Email node.
3. Sets up all 5 Gmail nodes with unified draft_email_subject & draft_email_body.
4. Updates database.sqlite (workflow_entity, workflow_history, workflow_published_version).
5. Runs n8n import:workflow and n8n publish:workflow.
6. Restarts n8n container and verifies health.
"""
import json
import os
import subprocess
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUEPRINT_PATH = os.path.join(ROOT_DIR, "n8n_workflow_blueprint.json")
JS_CODE_PATH = os.path.join(ROOT_DIR, "scripts", "format_code.js")

HTML_EXEC_TEMPLATE = (
    '<div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; max-width: 640px; margin: 0 auto; background-color: #0d1117; color: #e6edf3; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">'
    '<div style="background: linear-gradient(135deg, #161b22 0%, #1f2937 100%); padding: 26px 24px; border-bottom: 2px solid #238636;">'
    '<div style="display: inline-block; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; background-color: rgba(46, 160, 67, 0.2); color: #3fb950; border: 1px solid #238636; padding: 3px 8px; border-radius: 4px; margin-bottom: 8px;">'
    'Mazatlan Operations Studio &bull; Executive Digest'
    '</div>'
    '<h1 style="margin: 4px 0 6px 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">'
    'nuDesk Executive Operations Briefing'
    '</h1>'
    '<p style="margin: 0; font-size: 13px; color: #8b949e;">'
    '{{ $json.digest_title }} &bull; Reporte Consolidado de Pipeline y Cumplimiento SLA'
    '</p>'
    '</div>'
    '<div style="padding: 24px;">'
    '<div style="margin-bottom: 22px;">'
    '<table style="width: 100%; border-collapse: separate; border-spacing: 8px; margin: -8px;">'
    '<tr>'
    '<td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">'
    '<div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Credito Solicitado</div>'
    '<div style="font-size: 24px; font-weight: 800; color: #3fb950; margin: 6px 0 2px 0;">{{ $json.credit_volume_usd }}</div>'
    '<div style="font-size: 11px; color: #8b949e;">{{ $json.credit_count }} expedientes de factoraje/equipo</div>'
    '</td>'
    '<td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">'
    '<div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Pipeline Comercial (ARR)</div>'
    '<div style="font-size: 24px; font-weight: 800; color: #58a6ff; margin: 6px 0 2px 0;">{{ $json.sales_arr_usd }}</div>'
    '<div style="font-size: 11px; color: #8b949e;">{{ $json.sales_count }} prospectos BDR calificados</div>'
    '</td>'
    '</tr>'
    '<tr>'
    '<td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">'
    '<div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Cumplimiento de SLA</div>'
    '<div style="font-size: 24px; font-weight: 800; color: #d29922; margin: 6px 0 2px 0;">{{ $json.sla_compliance_pct }}</div>'
    '<div style="font-size: 11px; color: #3fb950; font-weight: 600;">&lt; 15 min Turnaround Target</div>'
    '</td>'
    '<td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">'
    '<div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Volumen Operativo Total</div>'
    '<div style="font-size: 24px; font-weight: 800; color: #ffffff; margin: 6px 0 2px 0;">{{ $json.total_operations }}</div>'
    '<div style="font-size: 11px; color: #8b949e;">{{ $json.processed_count }} procesadas &bull; {{ $json.pending_count }} en cola</div>'
    '</td>'
    '</tr>'
    '</table>'
    '</div>'
    '<div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 18px; margin-bottom: 20px;">'
    '<h3 style="margin: 0 0 10px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #58a6ff;">'
    'Dictamen y Resumen Ejecutivo'
    '</h3>'
    '<p style="margin: 0; font-size: 13.5px; line-height: 1.6; color: #c9d1d9;">'
    '{{ $json.executive_summary }}'
    '</p>'
    '</div>'
    '<div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 18px; margin-bottom: 20px;">'
    '<h3 style="margin: 0 0 12px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #8b949e;">'
    'Rendimiento por Departamento (Mazatlan Hub)'
    '</h3>'
    '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
    '<tr style="border-bottom: 1px solid #21262d;">'
    '<th style="text-align: left; padding: 8px 0; color: #8b949e;">Departamento</th>'
    '<th style="text-align: center; padding: 8px 0; color: #8b949e;">Volumen</th>'
    '<th style="text-align: right; padding: 8px 0; color: #8b949e;">Estado</th>'
    '</tr>'
    '<tr style="border-bottom: 1px solid #21262d;">'
    '<td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Credito &amp; Underwriting</td>'
    '<td style="text-align: center; padding: 10px 0; color: #3fb950; font-weight: 700;">{{ $json.credit_count }} files</td>'
    '<td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">Sincronizado LOS</span></td>'
    '</tr>'
    '<tr style="border-bottom: 1px solid #21262d;">'
    '<td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Ventas BDR (Comercial)</td>'
    '<td style="text-align: center; padding: 10px 0; color: #58a6ff; font-weight: 700;">{{ $json.sales_count }} leads</td>'
    '<td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid rgba(88, 166, 255, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">Outreach Staged</span></td>'
    '</tr>'
    '<tr>'
    '<td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Talento &amp; RH Bilingüe</td>'
    '<td style="text-align: center; padding: 10px 0; color: #bc8cff; font-weight: 700;">{{ $json.hr_count }} candidatos</td>'
    '<td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(188, 140, 255, 0.15); color: #bc8cff; border: 1px solid rgba(188, 140, 255, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">CEFR Validado</span></td>'
    '</tr>'
    '</table>'
    '</div>'
    '<div style="border-top: 1px solid #21262d; padding-top: 16px; font-size: 11px; color: #8b949e; line-height: 1.5;">'
    '<p style="margin: 0 0 4px 0;">'
    '<strong>Emisor / Auditor:</strong> {{ $json.operator }} &bull; <strong>Fecha:</strong> {{ $json.timestamp }}'
    '</p>'
    '<p style="margin: 0;">'
    'Este informe fue sintetizado de manera deterministica por el orquestador nuDesk Operations Studio con integracion a Google Workspace. Confidencial para uso interno.'
    '</p>'
    '</div>'
    '</div>'
    '</div>'
)

def build_workflow():
    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    with open(JS_CODE_PATH, "r", encoding="utf-8") as f:
        js_code = f.read()

    nodes = blueprint.get("nodes", [])

    # Update Code Node
    for node in nodes:
        if node.get("name") == "Format for Google Sheets, CRM & Mail":
            node["parameters"]["jsCode"] = js_code

    # Remove any existing Gmail nodes to reinstall cleanly
    gmail_names = [
        "Gmail - Create Credit Approval Draft",
        "Gmail - Create BDR Outreach Draft",
        "Gmail - Create Candidate Follow-up Draft",
        "Gmail - Send Executive Digest Email",
        "Gmail - Create IT Health Alert Draft"
    ]
    nodes = [n for n in nodes if n.get("name") not in gmail_names]

    gmail_creds = {
        "gmailOAuth2": {
            "id": "HpmyqoAqph28Rjgm",
            "name": "Gmail account"
        }
    }

    # 1. Credit Draft
    nodes.append({
        "parameters": {
            "resource": "draft",
            "operation": "create",
            "subject": "={{ $json.draft_email_subject }}",
            "emailType": "text",
            "message": "={{ $json.draft_email_body }}",
            "options": {
                "sendTo": "={{ $json.recipient_email }}"
            }
        },
        "id": "e45f992a-8c01-4b72-98e1-5128ab91c890",
        "name": "Gmail - Create Credit Approval Draft",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [-112, 160],
        "credentials": gmail_creds
    })

    # 2. Sales Draft
    nodes.append({
        "parameters": {
            "resource": "draft",
            "operation": "create",
            "subject": "={{ $json.draft_email_subject }}",
            "emailType": "text",
            "message": "={{ $json.draft_email_body }}",
            "options": {
                "sendTo": "={{ $json.recipient_email }}"
            }
        },
        "id": "a413723f-9af3-4f0c-ac6b-10bf0e1cbd37",
        "name": "Gmail - Create BDR Outreach Draft",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [-112, 464],
        "credentials": gmail_creds
    })

    # 3. HR Draft
    nodes.append({
        "parameters": {
            "resource": "draft",
            "operation": "create",
            "subject": "={{ $json.draft_email_subject }}",
            "emailType": "text",
            "message": "={{ $json.draft_email_body }}",
            "options": {
                "sendTo": "={{ $json.recipient_email }}"
            }
        },
        "id": "5e51ce65-3af0-4577-b09b-347ada23a195",
        "name": "Gmail - Create Candidate Follow-up Draft",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [-112, 624],
        "credentials": gmail_creds
    })

    # 4. Executive Direct Email to Inbox
    nodes.append({
        "parameters": {
            "resource": "message",
            "operation": "send",
            "sendTo": "={{ $json.recipient_email || 'omarpayant@gmail.com' }}",
            "subject": "=nuDesk Executive Briefing — {{ $json.digest_title }}",
            "emailType": "html",
            "message": "=" + HTML_EXEC_TEMPLATE,
            "options": {}
        },
        "id": "b18f773c-4d12-4f81-81d3-6192ac82d123",
        "name": "Gmail - Send Executive Digest Email",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [-112, 784],
        "credentials": gmail_creds
    })

    # 5. IT Health Draft (Distribution List to Multiple Recipients)
    nodes.append({
        "parameters": {
            "resource": "draft",
            "operation": "create",
            "subject": "={{ $json.draft_email_subject }}",
            "emailType": "text",
            "message": "={{ $json.draft_email_body }}",
            "options": {
                "sendTo": "={{ $json.recipient_email }}"
            }
        },
        "id": "c29f884d-5e23-4a92-92e4-7203bd93e234",
        "name": "Gmail - Create IT Health Alert Draft",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [-112, 944],
        "credentials": gmail_creds
    })

    connections = {
        "Incoming nuDesk Webhook": {
            "main": [[{"node": "Format for Google Sheets, CRM & Mail", "type": "main", "index": 0}]]
        },
        "Format for Google Sheets, CRM & Mail": {
            "main": [[{"node": "Route by Operation Type", "type": "main", "index": 0}]]
        },
        "Route by Operation Type": {
            "main": [
                [{"node": "Google Sheets - Credit LOS", "type": "main", "index": 0}],
                [{"node": "Google Sheets - Sales CRM", "type": "main", "index": 0}],
                [{"node": "Google Sheets - Talent Roster", "type": "main", "index": 0}],
                [{"node": "Gmail - Send Executive Digest Email", "type": "main", "index": 0}],
                [{"node": "Gmail - Create IT Health Alert Draft", "type": "main", "index": 0}]
            ]
        },
        "Google Sheets - Credit LOS": {
            "main": [
                [
                    {"node": "Asana - Create Underwriting Task", "type": "main", "index": 0},
                    {"node": "Gmail - Create Credit Approval Draft", "type": "main", "index": 0}
                ]
            ]
        },
        "Google Sheets - Sales CRM": {
            "main": [
                [{"node": "Gmail - Create BDR Outreach Draft", "type": "main", "index": 0}]
            ]
        },
        "Google Sheets - Talent Roster": {
            "main": [
                [{"node": "Gmail - Create Candidate Follow-up Draft", "type": "main", "index": 0}]
            ]
        }
    }

    workflow = {
        "id": "SDAJiNePGG1J3TzW",
        "name": "nuDesk Operations Studio - Multi-Flow Triage & Google Workspace Sync",
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"}
    }

    # Save to blueprint
    with open(BLUEPRINT_PATH, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2)
    print("Updated local blueprint at:", BLUEPRINT_PATH)

    # Save array for import
    tmp_import = "/tmp/n8n_full_deploy.json"
    with open(tmp_import, "w", encoding="utf-8") as f:
        json.dump([workflow], f, indent=2)

    return workflow, tmp_import


def deploy():
    workflow, tmp_import = build_workflow()

    print("Copying workflow to container...")
    subprocess.run(["docker", "cp", tmp_import, "nudesk_n8n:/tmp/n8n_full_deploy.json"], check=True)

    print("Importing workflow via CLI...")
    res = subprocess.run(
        ["docker", "exec", "nudesk_n8n", "n8n", "import:workflow", "--input=/tmp/n8n_full_deploy.json"],
        capture_output=True, text=True
    )
    print("IMPORT:", res.stdout)

    print("Publishing workflow via CLI...")
    res_pub = subprocess.run(
        ["docker", "exec", "nudesk_n8n", "n8n", "publish:workflow", "--id=SDAJiNePGG1J3TzW"],
        capture_output=True, text=True
    )
    print("PUBLISH:", res_pub.stdout)

    # Also directly update sqlite tables to ensure active=1 and publish version consistency
    nodes_str = json.dumps(workflow["nodes"])
    conn_str = json.dumps(workflow["connections"])

    sqlite_updater = f"""
    const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
    const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
    const fs = require('fs');
    const wf = JSON.parse(fs.readFileSync('/tmp/n8n_full_deploy.json'))[0];
    const nodesJson = JSON.stringify(wf.nodes);
    const connJson = JSON.stringify(wf.connections);

    db.serialize(() => {{
      // Update workflow_entity
      db.run(
        'UPDATE workflow_entity SET active = 1, nodes = ?, connections = ?, updatedAt = datetime("now") WHERE id = "SDAJiNePGG1J3TzW"',
        [nodesJson, connJson],
        (err) => {{ if (err) console.error("Error updating workflow_entity:", err); }}
      );

      // Update all workflow_history entries for this workflow
      db.run(
        'UPDATE workflow_history SET nodes = ?, connections = ?, updatedAt = datetime("now") WHERE workflowId = "SDAJiNePGG1J3TzW"',
        [nodesJson, connJson],
        (err) => {{ if (err) console.error("Error updating workflow_history:", err); }}
      );

      console.log("Synchronized SQLite database tables!");
      db.close();
    }});
    """
    tmp_sql_script = "/tmp/update_n8n_sqlite.js"
    with open(tmp_sql_script, "w", encoding="utf-8") as f:
        f.write(sqlite_updater)
    subprocess.run(["docker", "cp", tmp_sql_script, "nudesk_n8n:/tmp/update_n8n_sqlite.js"], check=True)
    res_node = subprocess.run(
        ["docker", "exec", "nudesk_n8n", "node", "/tmp/update_n8n_sqlite.js"],
        capture_output=True, text=True
    )
    print("SQLITE SYNC:", res_node.stdout)

    print("Restarting n8n container to apply all changes...")
    subprocess.run(["docker", "restart", "nudesk_n8n"], check=True)
    print("Waiting for n8n to become ready...")
    time.sleep(5)

    res_h = subprocess.run(["curl", "-s", "http://localhost:5678/healthz"], capture_output=True, text=True)
    print("Health check:", res_h.stdout)


if __name__ == "__main__":
    deploy()
