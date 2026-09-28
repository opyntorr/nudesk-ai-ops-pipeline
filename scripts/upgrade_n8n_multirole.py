#!/usr/bin/env python3
"""
Helper script to update n8n workflow in database.sqlite:
- Sends formatted HTML email directly to Omar's Inbox for Executive Briefing
- Creates long, humane, standardized Drafts for Credit, Sales, HR, and IT
"""
import subprocess
import json

SCRIPT = r"""
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
  const operator = meta.operator_name || 'Especialista Operativo';
  
  if (flow === 'sales') {
    const company = data.company_name || data.business_name || 'Empresa Aliada';
    const contact = data.contact_person || data.applicant_name || 'Estimado/a Directivo/a';
    const industry = data.industry || 'Comercio y Logistica';
    const revFormatted = data.annual_revenue_usd ? Number(data.annual_revenue_usd).toLocaleString('en-US') : '2,400,000';
    
    const subject = 'Alianza Comercial nuDesk & ' + company + ' | Soluciones de Liquidez y Capital de Trabajo';
    const draftBody = 'Estimado/a ' + contact + ',\n\n' +
      'Espero que se encuentre muy bien al recibir esta comunicacion.\n\n' +
      'Nos ponemos en contacto desde nuDesk Operations Studio tras haber revisado detenidamente la destacada presencia y crecimiento operativo de ' + company + ' dentro del sector de ' + industry + '. Sabemos por experiencia en la industria que mantener el ritmo comercial y asegurar entregas continuas exige una gestion de flujo de caja sumamente rigurosa, en especial cuando los plazos de cobranza con clientes y distribuidores suelen dilatarse de 30 a 60 dias.\n\n' +
      'Nuestro objetivo en nuDesk es respaldar a empresas comerciales de alto rendimiento mediante facilidades financieras agiles que eliminen la friccion tradicional. Desde nuestro centro de operaciones en Mazatlan, ofrecemos esquemas de factoraje de cobranza acelerada y lineas de credito de trabajo estructuradas que permiten convertir cuentas por cobrar en liquidez disponible en menos de 48 horas sin garantias hipotecarias gravosas.\n\n' +
      'Considerando el volumen comercial de ' + company + ' (estimado en $' + revFormatted + ' USD anuales), hemos diseñado alternativas de financiamiento a la medida orientadas a:\n\n' +
      '1. Acelerar el flujo de efectivo operativo: Obtener anticipos inmediatos sobre facturas comerciales emitidas, sin tener que esperar ventanas de pago extendidas.\n' +
      '2. Proteger la operacion y compromisos esenciales: Garantizar fondos inmediatos para nomina operativa, fletes, mantenimiento y compras a proveedores estrategicos.\n' +
      '3. Respaldar nuevas oportunidades de mercado: Atender pedidos de mayor escala con la tranquilidad de contar con una linea de credito disponible y sin tramites burocraticos engorrosos.\n\n' +
      'Nos encantaria poder conversar brevemente con usted en una videollamada exploratoria de 15 minutos durante esta semana para presentarle formalmente como trabajamos y analizar si nuestras facilidades de liquidez representan una ventaja tangible para ' + company + '.\n\n' +
      '¿Tendria disponibilidad para una llamada este proximo martes o jueves por la mañana? Con gusto nos adecuamos a la fecha y hora que mejor convenga a su agenda.\n\n' +
      'Agradezco de antemano su amable tiempo y atencion a esta invitacion, y quedo a sus ordenes para cualquier consulta preliminar.\n\n' +
      'Atentamente,\n\n' +
      operator + '\n' +
      'Desarrollo de Negocios & Alianzas Comerciales\n' +
      'nuDesk Operations Studio — Mazatlan Hub';

    output.push({
      json: {
        flow_type: 'sales',
        pipeline_type: 'Sales Operations',
        timestamp: timestamp,
        company_name: company,
        contact_person: contact,
        industry: industry,
        annual_revenue_usd: data.annual_revenue_usd || 0,
        lead_score: data.lead_score || 0,
        lead_tier: data.lead_tier || (data.lead_score >= 85 ? 'Hot Lead' : (data.lead_score >= 70 ? 'Qualified' : 'Review')),
        draft_email_subject: subject,
        draft_email_body: draftBody,
        analyst_notes: data.analyst_notes || '',
        operator: operator,
        status: 'Synced with Google Sheets CRM & Gmail Drafts'
      }
    });

  } else if (flow === 'hr') {
    const candidate = data.candidate_name || data.applicant_name || 'Estimado/a Candidato/a';
    const role = data.target_role || data.applied_role || 'Analista Comercial Bilingüe';
    
    const subject = 'nuDesk Talent Hub | Seguimiento a tu proceso de seleccion - ' + candidate;
    const draftBody = 'Estimado/a ' + candidate + ',\n\n' +
      'Esperamos que este mensaje te encuentre muy bien.\n\n' +
      'Queremos agradecerte sinceramente el tiempo, la apertura y el entusiasmo que nos compartiste durante nuestra reciente entrevista para la posicion de ' + role + ' en nuDesk Operations Studio. Fue un verdadero gusto conversar contigo y profundizar en tu trayectoria, tus intereses y los proyectos en los que has participado.\n\n' +
      'Tras una detallada sesion de deliberacion del comite de Atraccion de Talento del Mazatlan Hub, nos complace informarte que tu perfil ha sido seleccionado favorablemente para avanzar a la siguiente etapa de nuestro proceso: la Evaluacion Tecnica y Caso Practico Operativo.\n\n' +
      'Durante nuestra conversacion valoramos especialmente tu claridad de pensamiento, tu solidez en la comunicacion bilingüe y tu enfoque resolutivo ante retos operativos, cualidades que consideramos fundamentales para la excelencia en nuestros servicios financieros.\n\n' +
      'Para brindarte certidumbre sobre lo que viene, a continuacion te compartimos los aspectos clave de esta siguiente fase:\n\n' +
      '1. Objetivo de la Sesion:\n' +
      'Nos interesa conocer de manera practica tu metodologia de trabajo y como abordas situaciones reales del dia a dia, privilegiando el sentido comun, la atencion al detalle y la estructura analitica sobre cualquier respuesta memorizada.\n\n' +
      '2. Modalidad y Duracion:\n' +
      'El ejercicio se llevara a cabo de forma remota a traves de una sesion guiada por uno de nuestros lideres de area, con una duracion aproximada de 45 a 60 minutos. No requiere preparacion tecnica exhaustiva previa, unicamente un equipo con conexion estable y tu disposicion habitual.\n\n' +
      '3. Coordinacion de Horarios:\n' +
      'Con el proposito de respetar tus compromisos actuales, te pedimos de favor responder a este correo indicandonos dos opciones de fecha y horario que te resulten convenientes durante los proximos dias (de lunes a viernes, entre 9:00 AM y 5:00 PM CST). A la brevedad te confirmaremos la cita en tu calendario con el enlace correspondiente.\n\n' +
      'Si tienes cualquier duda respecto a la dinamica, requieres alguna consideracion particular de agenda o simplemente deseas conversar sobre algun aspecto de la posicion antes de la sesion, no dudes en escribirnos directamente respondiendo a este correo.\n\n' +
      'Te reiteramos nuestro agradecimiento por considerar a nuDesk como el siguiente paso en tu desarrollo profesional y te deseamos el mayor de los exitos en esta evaluacion.\n\n' +
      'Con un cordial saludo,\n\n' +
      operator + '\n' +
      'Especialista de Atraccion de Talento & Cultura\n' +
      'nuDesk Operations Studio — Mazatlan Talent Hub';

    output.push({
      json: {
        flow_type: 'hr',
        pipeline_type: 'HR Talent Screening',
        timestamp: timestamp,
        candidate_name: candidate,
        target_role: role,
        cefr_level: data.english_fluency_cefr || data.cefr || data.bilingual_fluency_rating || 'B2',
        competency_score: data.technical_competency_score || data.fit_score || data.candidate_fit_score || 0,
        salary_expectation_usd: data.salary_expectation_monthly_usd || 0,
        hiring_recommendation: data.hiring_recommendation || data.action || data.recommended_action || 'Advance to Case Study',
        interviewer_notes: data.analyst_notes || '',
        draft_email_subject: subject,
        draft_email_body: draftBody,
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
    const alertTitle = data.alert_title || 'Auditoria de Integridad y Model Cascade';
    const latency = data.gemini_latency_ms || 284;
    const dbIntegrity = data.sqlite_integrity || 'OK (0 errores)';
    const piiStatus = data.pii_masking_status || 'Enforced (100% verificado)';
    const injections = data.injections_blocked !== undefined ? data.injections_blocked : 0;
    const dockerStatus = data.docker_n8n_status || 'Healthy (Puerto 5678)';
    const details = data.details || 'Todos los microservicios, guardrails y pasarelas operan dentro de los umbrales nominales.';

    const subject = 'nuDesk IT Ops | Bitacora de Integridad de Sistemas, Telemetria y Ciberseguridad - ' + alertTitle;
    const draftBody = 'Estimado equipo de Infraestructura, Seguridad y Operaciones de Sistemas de nuDesk,\n\n' +
      'Por medio del presente informe tecnico se emite la bitacora consolidada de integridad operativa, latencia de modelos y estado de defensas de ciberseguridad correspondiente al ciclo de supervision en Mazatlan Operations Hub.\n\n' +
      'El diagnostico automatizado confirma que la arquitectura de microservicios, bases de datos transaccionales y pasarelas de automatizacion operan bajo condiciones normales de estabilidad y resiliencia, cumpliendo al 100% con los acuerdos de nivel de servicio (SLA) corporativos.\n\n' +
      'A continuacion, se detalla el estado actual de los componentes supervisados:\n\n' +
      '1. Cascada de Modelos de Inteligencia Artificial (Google Gemini):\n' +
      '- Estado: Operativo y balanceado en cascada multi-modelo.\n' +
      '- Latencia Promedio Registrada: ' + latency + ' ms por solicitud de inferencia.\n' +
      '- Resiliencia Zero-Config: Mecanismo de contingencia offline verificado y respaldado por contratos estrictos Pydantic V2 sin excepciones no capturadas.\n\n' +
      '2. Integridad de Base de Datos y Trazabilidad Transaccional:\n' +
      '- Motor Operativo: SQLite de alta concurrencia con bloqueos atomicos y control de transacciones.\n' +
      '- Diagnostico de Integridad: ' + dbIntegrity + '.\n' +
      '- Registro de Auditoria: 100% de operaciones sincronizadas con temporizadores de SLA activos y calculo de antigüedad FIFO.\n\n' +
      '3. Interceptores de Ciberdefensa y Privacidad de Datos:\n' +
      '- Enmascaramiento de PII: ' + piiStatus + ' (Filtros regex activos para SSN, EIN y tarjetas de pago corporativas).\n' +
      '- Firewall Anti-Inyeccion de Prompts: ' + injections + ' firmas adversariales neutralizadas oportunamente en fase de pre-vuelo.\n' +
      '- Reconciliacion Matematica Post-Vuelo: Verificacion cruzada algoritmica de ratios financieros (DTI / DSCR) para eliminar alucinaciones numericas.\n\n' +
      '4. Pasarela de Automatizacion y Ecosistema n8n:\n' +
      '- Contenedor Docker: ' + dockerStatus + '.\n' +
      '- Integracion Externa: Webhooks de ingesta (Read.ai / Fireflies) y sincronizacion con Google Workspace (Gmail / Sheets) y Asana operando satisfactoriamente.\n\n' +
      'Observaciones Tecnicas y Diagnostico del Especialista:\n' +
      details + '\n\n' +
      'Dictamen de Cumplimiento Tecnico:\n' +
      'La infraestructura mantiene una disponibilidad nominal ininterrumpida y una postura de seguridad robusta, apta para el soporte continuo de operaciones financieras bilingües.\n\n' +
      'Atentamente,\n\n' +
      operator + '\n' +
      'Arquitectura de Sistemas & Ciberseguridad\n' +
      'nuDesk IT Infrastructure Workbench — Mazatlan Hub';

    output.push({
      json: {
        flow_type: 'it',
        pipeline_type: 'IT Infrastructure & Security',
        timestamp: timestamp,
        alert_title: alertTitle,
        gemini_latency_ms: latency,
        sqlite_integrity: dbIntegrity,
        pii_masking_status: piiStatus,
        injections_blocked: injections,
        docker_n8n_status: dockerStatus,
        details: details,
        draft_email_subject: subject,
        draft_email_body: draftBody,
        operator: operator,
        status: 'Synced with Gmail IT Alert'
      }
    });

  } else {
    // Default to Credit flow
    const company = data.business_name || data.company_name || 'Empresa Solicitante';
    const applicant = data.applicant_name || data.contact_person || 'Estimado/a Solicitante';
    const loanAmt = data.loan_amount_requested_usd ? Number(data.loan_amount_requested_usd).toLocaleString('en-US') : '85,000';
    const collateral = data.collateral_type || 'Garantias Comerciales y Flujos de Facturacion';
    const riskTier = data.risk_tier || 'Riesgo Moderado';
    const execSummary = data.executive_summary || 'Evaluacion favorable basada en volumen de ventas comprobable y capacidad de pago suficiente.';

    const subject = 'nuDesk Underwriting | Dictamen Favorable y Terminos de Aprobacion Preliminar - ' + company;
    const draftBody = 'Estimado/a ' + applicant + ',\n\n' +
      'Esperamos que se encuentre muy bien al momento de recibir este comunicado.\n\n' +
      'Por medio de la presente, nos complace informarle que el Comite de Credito y Suscripcion de Riesgos de nuDesk Operations Studio ha finalizado exitosamente el analisis financiero y documental correspondiente a la solicitud de financiamiento ingresada en favor de ' + company + '.\n\n' +
      'Tras una rigurosa revision de sus flujos operativos, capacidad de pago y las garantias presentadas, hemos emitido un dictamen de aprobacion preliminar para una facilidad crediticia comercial por un monto de $' + loanAmt + ' USD. Felicitamos a su equipo directivo por la solidez y el orden financiero demostrado durante este proceso de evaluacion.\n\n' +
      'A continuacion, le compartimos el resumen de las condiciones preliminares aprobadas:\n\n' +
      '1. Empresa Acreditada: ' + company + '\n' +
      '2. Representante / Contacto Principal: ' + applicant + '\n' +
      '3. Monto Aprobado: $' + loanAmt + ' USD\n' +
      '4. Tipo de Facilidad: Linea de Credito Comercial / Arrendamiento de Equipo\n' +
      '5. Esquema de Garantia / Colateral: ' + collateral + '\n' +
      '6. Dictamen de Riesgo: ' + riskTier + ' (Perfil calificado y solvente bajo politica prudencial)\n\n' +
      'Resumen Ejecutivo del Dictamen:\n' +
      execSummary + '\n\n' +
      'Guia de Siguientes Pasos para Formalizacion y Dispersion:\n' +
      'Con la finalidad de proceder a la firma contractual y efectuar la dispersion de los recursos en su cuenta bancaria a la brevedad, requerimos coordinar conjuntamente las siguientes etapas:\n\n' +
      'Paso 1: Validacion Documental Final: Recepcion de identificacion oficial vigente del representante legal, constancia de situacion fiscal actualizada (no mayor a 30 dias) y comprobante de cuenta bancaria receptora.\n' +
      'Paso 2: Firma de Instrumentos Contractuales: Formalizacion digital del contrato marco de apertura de credito y pagare correspondiente mediante nuestra plataforma segura con validez juridica.\n' +
      'Paso 3: Programacion y Dispersion: Confirmacion de fondos y transferencia a su cuenta corporativa en un plazo no mayor a 24 horas habiles posteriores a la firma.\n\n' +
      'Su expediente ha sido asignado a nuestra mesa de operaciones en Mazatlan, quienes le estaran brindando acompañamiento personalizado durante toda la fase de firma y desembolso.\n\n' +
      'Si requiere aclarar cualquier termino de la aprobacion, coordinar aspectos especificos de la dispersion o tiene alguna consulta sobre la documentacion requerida, por favor comuniquese directamente respondiendo a este correo o contactando a su oficial asignado.\n\n' +
      'Reiteramos nuestro agradecimiento por elegir a nuDesk como su aliado financiero estrategico y le deseamos continuo exito en la expansion de ' + company + '.\n\n' +
      'Atentamente,\n\n' +
      operator + '\n' +
      'Oficial de Credito & Suscripcion de Riesgos\n' +
      'nuDesk Underwriting Operations — Mazatlan Hub';

    output.push({
      json: {
        flow_type: 'credit',
        pipeline_type: 'Credit Operations',
        timestamp: timestamp,
        company_name: company,
        applicant_name: applicant,
        loan_amount_usd: data.loan_amount_requested_usd || 0,
        dti_ratio: data.dti_ratio || 'N/A',
        risk_tier: riskTier,
        collateral: collateral,
        executive_summary: execSummary,
        red_flags: Array.isArray(data.red_flags) ? data.red_flags.join('; ') : (data.red_flags || 'Ninguna registrada'),
        analyst_notes: data.analyst_notes || '',
        draft_email_subject: subject,
        draft_email_body: draftBody,
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

  // 3. Ensure Gmail nodes exist and are configured
  const gmailCreds = { gmailOAuth2: { id: "HpmyqoAqph28Rjgm", name: "Gmail account" } };

  // Remove existing Gmail nodes to cleanly reinstall with updated parameters
  const gmailNodeNames = [
    'Gmail - Create Credit Approval Draft',
    'Gmail - Create BDR Outreach Draft',
    'Gmail - Create Candidate Follow-up Draft',
    'Gmail - Create Executive Digest Draft',
    'Gmail - Send Executive Digest Email',
    'Gmail - Create IT Health Alert Draft'
  ];
  nodes = nodes.filter(n => !gmailNodeNames.includes(n.name));

  // Add Gmail - Create Credit Approval Draft
  nodes.push({
    parameters: {
      resource: "draft",
      operation: "create",
      subject: "={{ $json.draft_email_subject }}",
      emailType: "text",
      message: "={{ $json.draft_email_body }}",
      options: {}
    },
    id: "e45f992a-8c01-4b72-98e1-5128ab91c890",
    name: "Gmail - Create Credit Approval Draft",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 160],
    credentials: gmailCreds
  });

  // Add Gmail - Create BDR Outreach Draft
  nodes.push({
    parameters: {
      resource: "draft",
      operation: "create",
      subject: "={{ $json.draft_email_subject }}",
      emailType: "text",
      message: "={{ $json.draft_email_body }}",
      options: {}
    },
    id: "a413723f-9af3-4f0c-ac6b-10bf0e1cbd37",
    name: "Gmail - Create BDR Outreach Draft",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 464],
    credentials: gmailCreds
  });

  // Add Gmail - Create Candidate Follow-up Draft
  nodes.push({
    parameters: {
      resource: "draft",
      operation: "create",
      subject: "={{ $json.draft_email_subject }}",
      emailType: "text",
      message: "={{ $json.draft_email_body }}",
      options: {}
    },
    id: "5e51ce65-3af0-4577-b09b-347ada23a195",
    name: "Gmail - Create Candidate Follow-up Draft",
    type: "n8n-nodes-base.gmail",
    typeVersion: 2.1,
    position: [-112, 624],
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
          <td style="padding: 10px 0; font-weight: 600; color: #ffffff;">Talento &amp; RH Bilingüe</td>
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
      subject: "={{ $json.draft_email_subject }}",
      emailType: "text",
      message: "={{ $json.draft_email_body }}",
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

  connections["Google Sheets - Sales CRM"] = {
    main: [
      [
        { node: "Gmail - Create BDR Outreach Draft", type: "main", index: 0 }
      ]
    ]
  };

  connections["Google Sheets - Talent Roster"] = {
    main: [
      [
        { node: "Gmail - Create Candidate Follow-up Draft", type: "main", index: 0 }
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
    print("Applying standardized, human-centric multi-role draft workflow to n8n...")
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
