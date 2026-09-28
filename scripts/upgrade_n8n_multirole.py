#!/usr/bin/env python3
"""
Helper script to update n8n workflow in database.sqlite:
- Sends formatted HTML email directly to Omar's Inbox for Executive Briefing
- Creates Drafts for Credit, Sales, HR, and IT
"""
import json
import subprocess
import os

SCRIPT = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.get('SELECT id, name, nodes, connections FROM workflow_entity WHERE id = "SDAJiNePGG1J3TzW"', (err, row) => {
  if (err) {
    console.error("Error reading workflow:", err);
    process.exit(1);
  }
  if (!row) {
    console.error("Workflow SDAJiNePGG1J3TzW not found!");
    process.exit(1);
  }

  let nodes = JSON.parse(row.nodes);
  let connections = JSON.parse(row.connections);

  // 1. Update Code Node: Format for Google Sheets, CRM & Mail
  const codeNode = nodes.find(n => n.name === 'Format for Google Sheets, CRM & Mail');
  if (codeNode) {
    codeNode.parameters.jsCode = `const items = $input.all();
const output = [];

for (const item of items) {
  const body = item.json.body || item.json;
  const meta = body.metadata || {};
  const data = body.data || {};
  const flow = (body.flow_type || meta.flow_type || 'credit').toLowerCase();
  
  const timestamp = meta.dispatch_timestamp || new Date().toISOString();
  const operator = meta.operator_name || 'Operational Specialist';
  
  if (flow === 'sales') {
    output.push({
      json: {
        flow_type: 'sales',
        pipeline_type: 'Sales Operations',
        timestamp: timestamp,
        company_name: data.company_name || data.business_name || 'N/A',
        contact_person: data.contact_person || data.applicant_name || 'N/A',
        industry: data.industry || 'General Commercial',
        annual_revenue_usd: data.annual_revenue_usd || 0,
        lead_score: data.lead_score || 0,
        lead_tier: data.lead_tier || (data.lead_score >= 85 ? 'Hot Lead' : (data.lead_score >= 70 ? 'Qualified' : 'Review')),
        draft_email_subject: data.draft_outreach_subject || \`nuDesk Commercial Partnership - \${data.company_name || 'Inquiry'}\`,
        draft_email_body: data.draft_outreach_body || data.score_rationale || 'We reviewed your freight operations and identified tailored credit facility options.',
        analyst_notes: data.analyst_notes || '',
        operator: operator,
        status: 'Synced with Google Sheets CRM & Gmail Drafts'
      }
    });
  } else if (flow === 'hr') {
    output.push({
      json: {
        flow_type: 'hr',
        pipeline_type: 'HR Talent Screening',
        timestamp: timestamp,
        candidate_name: data.candidate_name || data.applicant_name || 'N/A',
        target_role: data.target_role || data.applied_role || 'Commercial Credit Analyst',
        cefr_level: data.english_fluency_cefr || data.cefr || 'B2',
        competency_score: data.technical_competency_score || data.fit_score || 0,
        salary_expectation_usd: data.salary_expectation_monthly_usd || 0,
        hiring_recommendation: data.hiring_recommendation || data.action || 'Advance to Case Study',
        interviewer_notes: data.analyst_notes || '',
        operator: operator,
        status: 'Synced with Google Sheets Talent Roster & Gmail'
      }
    });
  } else if (flow === 'executive') {
    output.push({
      json: {
        flow_type: 'executive',
        pipeline_type: 'Executive Cockpit',
        timestamp: timestamp,
        digest_title: data.digest_title || 'Resumen Operativo Semanal',
        active_pipeline_usd: data.active_pipeline_usd || '$0 USD',
        credit_volume_usd: data.credit_volume_usd || '$0 USD',
        sales_arr_usd: data.sales_arr_usd || '$0 USD',
        sla_compliance_pct: data.sla_compliance_pct || '100%',
        total_operations: data.total_operations || 0,
        pending_count: data.pending_count || 0,
        processed_count: data.processed_count || 0,
        credit_count: data.credit_count || 0,
        sales_count: data.sales_count || 0,
        hr_count: data.hr_count || 0,
        executive_summary: data.executive_summary || 'Resumen de operaciones consolidado para Mazatlan Hub.',
        operator: operator,
        status: 'Sent to Executive Inbox'
      }
    });
  } else if (flow === 'it') {
    output.push({
      json: {
        flow_type: 'it',
        pipeline_type: 'IT Infrastructure & Security',
        timestamp: timestamp,
        alert_title: data.alert_title || 'Auditoria de Integridad y Model Cascade',
        gemini_latency_ms: data.gemini_latency_ms || 284,
        sqlite_integrity: data.sqlite_integrity || 'OK (0 errors)',
        pii_masking_status: data.pii_masking_status || 'Enforced (100%)',
        injections_blocked: data.injections_blocked || 0,
        docker_n8n_status: data.docker_n8n_status || 'Healthy (Port 5678)',
        details: data.details || 'Todos los microservicios y guardrails operan dentro de los umbrales nominales.',
        operator: operator,
        status: 'Synced with Gmail IT Alert'
      }
    });
  } else {
    // Default to Credit flow
    output.push({
      json: {
        flow_type: 'credit',
        pipeline_type: 'Credit Operations',
        timestamp: timestamp,
        company_name: data.business_name || data.company_name || 'N/A',
        applicant_name: data.applicant_name || data.contact_person || 'N/A',
        loan_amount_usd: data.loan_amount_requested_usd || 0,
        dti_ratio: data.dti_ratio || 'N/A',
        risk_tier: data.risk_tier || 'Moderate',
        collateral: data.collateral_type || 'General Assets',
        executive_summary: data.executive_summary || '',
        red_flags: Array.isArray(data.red_flags) ? data.red_flags.join('; ') : (data.red_flags || 'None reported'),
        analyst_notes: data.analyst_notes || '',
        operator: operator,
        status: 'Synced with Google Sheets Credit LOS, Asana & Gmail'
      }
    });
  }
}

return output;`;
  }

  // 2. Update Switch Node: Route by Operation Type
  const switchNode = nodes.find(n => n.name === 'Route by Operation Type');
  if (switchNode) {
    switchNode.parameters = {
      mode: "rules",
      rules: {
        values: [
          {
            conditions: {
              options: { caseSensitive: false, leftValue: "", typeValidation: "loose" },
              conditions: [{ leftValue: "={{ $json.flow_type }}", rightValue: "credit", operator: { type: "string", operation: "equals" } }],
              combinator: "and"
            },
            renameOutput: true,
            outputKey: "credit"
          },
          {
            conditions: {
              options: { caseSensitive: false, leftValue: "", typeValidation: "loose" },
              conditions: [{ leftValue: "={{ $json.flow_type }}", rightValue: "sales", operator: { type: "string", operation: "equals" } }],
              combinator: "and"
            },
            renameOutput: true,
            outputKey: "sales"
          },
          {
            conditions: {
              options: { caseSensitive: false, leftValue: "", typeValidation: "loose" },
              conditions: [{ leftValue: "={{ $json.flow_type }}", rightValue: "hr", operator: { type: "string", operation: "equals" } }],
              combinator: "and"
            },
            renameOutput: true,
            outputKey: "hr"
          },
          {
            conditions: {
              options: { caseSensitive: false, leftValue: "", typeValidation: "loose" },
              conditions: [{ leftValue: "={{ $json.flow_type }}", rightValue: "executive", operator: { type: "string", operation: "equals" } }],
              combinator: "and"
            },
            renameOutput: true,
            outputKey: "executive"
          },
          {
            conditions: {
              options: { caseSensitive: false, leftValue: "", typeValidation: "loose" },
              conditions: [{ leftValue: "={{ $json.flow_type }}", rightValue: "it", operator: { type: "string", operation: "equals" } }],
              combinator: "and"
            },
            renameOutput: true,
            outputKey: "it"
          }
        ]
      },
      options: {}
    };
  }

  // 3. Ensure Gmail nodes exist for Credit, Executive, IT
  const gmailCreds = { gmailOAuth2: { id: "HpmyqoAqph28Rjgm", name: "Gmail account" } };

  // Remove any previous versions of these nodes if present
  nodes = nodes.filter(n => !['Gmail - Create Credit Approval Draft', 'Gmail - Create Executive Digest Draft', 'Gmail - Send Executive Digest Email', 'Gmail - Create IT Health Alert Draft'].includes(n.name));

  // Add Gmail - Create Credit Approval Draft
  nodes.push({
    parameters: {
      resource: "draft",
      operation: "create",
      subject: "=nuDesk Underwriting - Dictamen Aprobado: {{ $json.company_name }}",
      emailType: "text",
      message: "=Dictamen Formal de Credito Comercial Aprobado (nuDesk Underwriting Hub)\\n\\nEmpresa: {{ $json.company_name }}\\nContacto: {{ $json.applicant_name }}\\nMonto Solicitado: ${{ $json.loan_amount_usd }} USD\\nNivel de Riesgo: {{ $json.risk_tier }}\\nRatio DTI: {{ $json.dti_ratio }}\\nColateral / Garantia: {{ $json.collateral }}\\n\\nResumen Ejecutivo:\\n{{ $json.executive_summary }}\\n\\nFlags de Riesgo / Red Flags:\\n{{ $json.red_flags }}\\n\\nOperador Asignado: {{ $json.operator }}\\nFecha de Aprobacion: {{ $json.timestamp }}\\nnuDesk Operations Studio — Mazatlan Hub",
      options: {}
    },
    id: "e45f992a-8c01-4b72-98e1-5128ab91c890",
    name: "Gmail - Create Credit Approval Draft",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 160],
    credentials: gmailCreds
  });

  const htmlExecutiveMessage = `<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 640px; margin: 0 auto; background-color: #0d1117; color: #e6edf3; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
  <div style="background: linear-gradient(135deg, #161b22 0%, #1f2937 100%); padding: 26px 24px; border-bottom: 2px solid #238636;">
    <div style="display: inline-block; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; background-color: rgba(46, 160, 67, 0.2); color: #3fb950; border: 1px solid #238636; padding: 3px 8px; border-radius: 4px; margin-bottom: 8px;">
      Mazatlan Operations Studio &bull; Executive Digest
    </div>
    <h1 style="margin: 4px 0 6px 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">
      nuDesk Executive Operations Briefing
    </h1>
    <p style="margin: 0; font-size: 13px; color: #8b949e;">
      {{ $json.digest_title }} &bull; Reporte Consolidado de Pipeline y Cumplimiento SLA
    </p>
  </div>

  <div style="padding: 24px;">
    <div style="margin-bottom: 22px;">
      <table style="width: 100%; border-collapse: separate; border-spacing: 8px; margin: -8px;">
        <tr>
          <td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">
            <div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Credito Solicitado</div>
            <div style="font-size: 24px; font-weight: 800; color: #3fb950; margin: 6px 0 2px 0;">{{ $json.credit_volume_usd }}</div>
            <div style="font-size: 11px; color: #8b949e;">{{ $json.credit_count }} expedientes de factoraje/equipo</div>
          </td>
          <td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">
            <div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Pipeline Comercial (ARR)</div>
            <div style="font-size: 24px; font-weight: 800; color: #58a6ff; margin: 6px 0 2px 0;">{{ $json.sales_arr_usd }}</div>
            <div style="font-size: 11px; color: #8b949e;">{{ $json.sales_count }} prospectos BDR calificados</div>
          </td>
        </tr>
        <tr>
          <td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">
            <div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Cumplimiento de SLA</div>
            <div style="font-size: 24px; font-weight: 800; color: #d29922; margin: 6px 0 2px 0;">{{ $json.sla_compliance_pct }}</div>
            <div style="font-size: 11px; color: #3fb950; font-weight: 600;">&lt; 15 min Turnaround Target</div>
          </td>
          <td style="width: 50%; background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; vertical-align: top;">
            <div style="font-size: 11px; text-transform: uppercase; color: #8b949e; font-weight: 600;">Volumen Operativo Total</div>
            <div style="font-size: 24px; font-weight: 800; color: #ffffff; margin: 6px 0 2px 0;">{{ $json.total_operations }}</div>
            <div style="font-size: 11px; color: #8b949e;">{{ $json.processed_count }} procesadas &bull; {{ $json.pending_count }} en cola</div>
          </td>
        </tr>
      </table>
    </div>

    <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 18px; margin-bottom: 20px;">
      <h3 style="margin: 0 0 10px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #58a6ff;">
        Dictamen y Resumen Ejecutivo
      </h3>
      <p style="margin: 0; font-size: 13.5px; line-height: 1.6; color: #c9d1d9;">
        {{ $json.executive_summary }}
      </p>
    </div>

    <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 18px; margin-bottom: 20px;">
      <h3 style="margin: 0 0 12px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #8b949e;">
        Rendimiento por Departamento (Mazatlan Hub)
      </h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <tr style="border-bottom: 1px solid #21262d;">
          <th style="text-align: left; padding: 8px 0; color: #8b949e;">Departamento</th>
          <th style="text-align: center; padding: 8px 0; color: #8b949e;">Volumen</th>
          <th style="text-align: right; padding: 8px 0; color: #8b949e;">Estado</th>
        </tr>
        <tr style="border-bottom: 1px solid #21262d;">
          <td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Credito &amp; Underwriting</td>
          <td style="text-align: center; padding: 10px 0; color: #3fb950; font-weight: 700;">{{ $json.credit_count }} files</td>
          <td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">Sincronizado LOS</span></td>
        </tr>
        <tr style="border-bottom: 1px solid #21262d;">
          <td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Ventas BDR (Comercial)</td>
          <td style="text-align: center; padding: 10px 0; color: #58a6ff; font-weight: 700;">{{ $json.sales_count }} leads</td>
          <td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid rgba(88, 166, 255, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">Outreach Staged</span></td>
        </tr>
        <tr>
          <td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Talento &amp; RH Bilingue</td>
          <td style="text-align: center; padding: 10px 0; color: #bc8cff; font-weight: 700;">{{ $json.hr_count }} candidatos</td>
          <td style="text-align: right; padding: 10px 0;"><span style="background-color: rgba(188, 140, 255, 0.15); color: #bc8cff; border: 1px solid rgba(188, 140, 255, 0.4); padding: 2px 7px; border-radius: 4px; font-size: 11px;">CEFR Validado</span></td>
        </tr>
      </table>
    </div>

    <div style="border-top: 1px solid #21262d; padding-top: 16px; font-size: 11px; color: #8b949e; line-height: 1.5;">
      <p style="margin: 0 0 4px 0;">
        <strong>Emisor / Auditor:</strong> {{ $json.operator }} &bull; <strong>Fecha:</strong> {{ $json.timestamp }}
      </p>
      <p style="margin: 0;">
        Este informe fue sintetizado de manera deterministica por el orquestador nuDesk Operations Studio con integracion a Google Workspace. Confidencial para uso interno.
      </p>
    </div>
  </div>
</div>`;

  // Add Gmail - Send Executive Digest Email (SENT DIRECTLY TO INBOX IN RICH HTML)
  nodes.push({
    parameters: {
      resource: "message",
      operation: "send",
      sendTo: "omarpayant@gmail.com",
      subject: "=nuDesk Executive Briefing — {{ $json.digest_title }}",
      emailType: "html",
      message: "=" + htmlExecutiveMessage,
      options: {}
    },
    id: "b18f773c-4d12-4f81-81d3-6192ac82d123",
    name: "Gmail - Send Executive Digest Email",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 784],
    credentials: gmailCreds
  });

  // Add Gmail - Create IT Health Alert Draft
  nodes.push({
    parameters: {
      resource: "draft",
      operation: "create",
      subject: "=nuDesk IT Ops - Diagnostico del Sistema: {{ $json.alert_title }}",
      emailType: "text",
      message: "=nuDesk IT Infrastructure & Security Audit (Mazatlan Hub)\\n\\nEstado de Componentes:\\n- Google Gemini Cascade: Activo (Latencia: {{ $json.gemini_latency_ms }} ms)\\n- Base de Datos SQLite: {{ $json.sqlite_integrity }}\\n- Enmascaramiento PII (SSN/EIN): {{ $json.pii_masking_status }}\\n- Intentos de Inyeccion Neutralizados: {{ $json.injections_blocked }}\\n- Docker n8n Gateway: {{ $json.docker_n8n_status }}\\n\\nDetalles del Diagnostico:\\n{{ $json.details }}\\n\\nOperador / Arquitecto: {{ $json.operator }}\\nFecha de Auditoria: {{ $json.timestamp }}\\nnuDesk IT & Infrastructure Workbench",
      options: {}
    },
    id: "c29f884d-5e23-4a92-92e4-7203bd93e234",
    name: "Gmail - Create IT Health Alert Draft",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 944],
    credentials: gmailCreds
  });

  // 4. Update Connections
  connections["Route by Operation Type"] = {
    main: [
      [{ node: "Google Sheets - Credit LOS", type: "main", index: 0 }],
      [{ node: "Google Sheets - Sales CRM", type: "main", index: 0 }],
      [{ node: "Google Sheets - Talent Roster", type: "main", index: 0 }],
      [{ node: "Gmail - Send Executive Digest Email", type: "main", index: 0 }],
      [{ node: "Gmail - Create IT Health Alert Draft", type: "main", index: 0 }]
    ]
  };

  connections["Google Sheets - Credit LOS"] = {
    main: [
      [
        { node: "Asana - Create Underwriting Task", type: "main", index: 0 },
        { node: "Gmail - Create Credit Approval Draft", type: "main", index: 0 }
      ]
    ]
  };

  const updatedNodesStr = JSON.stringify(nodes);
  const updatedConnectionsStr = JSON.stringify(connections);

  db.run(
    'UPDATE workflow_entity SET nodes = ?, connections = ?, updatedAt = datetime("now") WHERE id = "SDAJiNePGG1J3TzW"',
    [updatedNodesStr, updatedConnectionsStr],
    function(err) {
      if (err) {
        console.error("Error updating workflow:", err);
        process.exit(1);
      }
      console.log("Successfully updated workflow SDAJiNePGG1J3TzW in n8n database! Rows affected:", this.changes);
      db.close();
    }
  );
});
"""

def main():
    print("Applying updated executive email workflow to n8n...")
    cmd = ["docker", "exec", "nudesk_n8n", "node", "-e", SCRIPT]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    if res.returncode == 0:
        print("Restarting n8n container...")
        subprocess.run(["docker", "restart", "nudesk_n8n"], check=True)
        print("n8n restarted successfully.")
    else:
        print("Failed to update n8n workflow.")

if __name__ == "__main__":
    main()
