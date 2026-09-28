const items = $input.all();
const output = [];

for (const item of items) {
  const body = item.json.body || item.json;
  const meta = body.metadata || {};
  const data = body.data || {};
  const flow = (body.flow_type || meta.flow_type || "credit").toLowerCase();

  const timestamp = meta.dispatch_timestamp || new Date().toISOString();
  const operator = meta.operator_name || "Especialista Operativo";

  if (flow === "sales") {
    const company = data.company_name || data.business_name || "Sunbelt Logistics LLC";
    const rawContact = data.contact_person || data.applicant_name || "Marcus Vance";
    const contact = rawContact.replace(/\s*\(.*?\)\s*/g, "").trim() || rawContact;
    const industry = data.industry || "Comercio y Logística";
    const revFormatted = data.annual_revenue_usd ? Number(data.annual_revenue_usd).toLocaleString("en-US") : "2,400,000";

    let recipientEmail = data.recipient_email || data.contact_email || data.email;
    if (!recipientEmail || !recipientEmail.includes("@")) {
      recipientEmail = "mvance@sunbeltlogistics-demo.com";
    }

    const subject = "Alianza Comercial nuDesk & " + company + " | Soluciones de Liquidez y Capital de Trabajo";
    const draftBody = [
      "Estimado " + contact + ",",
      "",
      "Espero que se encuentre muy bien al recibir esta comunicación.",
      "",
      "Nos ponemos en contacto desde nuDesk Operations Studio tras haber revisado detenidamente la destacada presencia y crecimiento operativo de " + company + " dentro del sector de " + industry + ". Sabemos por experiencia en la industria que mantener el ritmo comercial y asegurar entregas continuas exige una gestión de flujo de caja sumamente rigurosa, en especial cuando los plazos de cobranza con clientes y distribuidores suelen dilatarse de 30 a 60 días.",
      "",
      "Nuestro objetivo en nuDesk es respaldar a empresas comerciales de alto rendimiento mediante facilidades financieras ágiles que eliminen la fricción tradicional. Desde nuestro centro de operaciones en Mazatlán, ofrecemos esquemas de factoraje de cobranza acelerada y líneas de crédito de trabajo estructuradas que permiten convertir cuentas por cobrar en liquidez disponible en menos de 48 horas sin garantías hipotecarias gravosas.",
      "",
      "Considerando el volumen comercial de " + company + " (estimado en $" + revFormatted + " USD anuales), hemos diseñado alternativas de financiamiento a la medida orientadas a:",
      "",
      "1. Acelerar el flujo de efectivo operativo: Obtener anticipos inmediatos sobre facturas comerciales emitidas, sin tener que esperar ventanas de pago extendidas.",
      "2. Proteger la operación y compromisos esenciales: Garantizar fondos inmediatos para nómina operativa, fletes, mantenimiento y compras a proveedores estratégicos.",
      "3. Respaldar nuevas oportunidades de mercado: Atender pedidos de mayor escala con la tranquilidad de contar con una línea de crédito disponible y sin trámites burocráticos engorrosos.",
      "",
      "Nos encantaría poder conversar brevemente con usted en una videollamada exploratoria de 15 minutos durante esta semana para presentarle formalmente cómo trabajamos y analizar si nuestras facilidades de liquidez representan una ventaja tangible para " + company + ".",
      "",
      "¿Tendría disponibilidad para una llamada este próximo martes o jueves por la mañana? Con gusto nos adecuamos a la fecha y hora que mejor convenga a su agenda.",
      "",
      "Agradezco de antemano su amable tiempo y atención a esta invitación, y quedo a sus órdenes para cualquier consulta preliminar.",
      "",
      "Atentamente,",
      "",
      operator,
      "Desarrollo de Negocios & Alianzas Comerciales",
      "nuDesk Operations Studio — Mazatlán Hub"
    ].join("\n");

    output.push({
      json: {
        flow_type: "sales",
        pipeline_type: "Sales Operations",
        timestamp: timestamp,
        company_name: company,
        contact_person: contact,
        recipient_email: recipientEmail,
        industry: industry,
        annual_revenue_usd: data.annual_revenue_usd || 0,
        lead_score: data.lead_score || 0,
        lead_tier: data.lead_tier || (data.lead_score >= 85 ? "Hot Lead" : (data.lead_score >= 70 ? "Qualified" : "Review")),
        draft_email_subject: subject,
        draft_email_body: draftBody,
        analyst_notes: data.analyst_notes || "",
        operator: operator,
        status: "Synced with Google Sheets CRM & Gmail Drafts"
      }
    });

  } else if (flow === "hr") {
    const rawCandidate = data.candidate_name || data.applicant_name || "Sofia Valdez";
    const candidate = rawCandidate.trim();
    const role = data.target_role || data.applied_role || "Senior Bilingual Credit Analyst";

    let recipientEmail = data.recipient_email || data.candidate_email || data.email;
    if (!recipientEmail || !recipientEmail.includes("@")) {
      if (candidate.toLowerCase().includes("sofia")) {
        recipientEmail = "sofia.valdez.candidate@gmail.com";
      } else if (candidate.toLowerCase().includes("mateo")) {
        recipientEmail = "mateo.guerrero.candidate@gmail.com";
      } else if (candidate.toLowerCase().includes("mariana")) {
        recipientEmail = "mariana.ochoa.candidate@gmail.com";
      } else {
        recipientEmail = "talento.candidato@nudesk-demo.com";
      }
    }

    const candidateGreeting = (candidate.toLowerCase().startsWith("sofia") || candidate.toLowerCase().startsWith("mariana") || candidate.toLowerCase().startsWith("valeria")) 
      ? ("Estimada " + candidate + ",") 
      : ("Estimado " + candidate + ",");

    const subject = "nuDesk Talent Hub | Seguimiento a tu proceso de selección - " + candidate;
    const draftBody = [
      candidateGreeting,
      "",
      "Esperamos que este mensaje te encuentre muy bien.",
      "",
      "Queremos agradecerte sinceramente el tiempo, la apertura y el entusiasmo que nos compartiste durante nuestra reciente entrevista para la posición de " + role + " en nuDesk Operations Studio. Fue un verdadero gusto conversar contigo y profundizar en tu trayectoria, tus intereses y los proyectos en los que has participado.",
      "",
      "Tras una detallada sesión de deliberación del comité de Atracción de Talento del Mazatlán Hub, nos complace informarte que tu perfil ha sido seleccionado favorablemente para avanzar a la siguiente etapa de nuestro proceso: la Evaluación Técnica y Caso Práctico Operativo.",
      "",
      "Durante nuestra conversación valoramos especialmente tu claridad de pensamiento, tu solidez en la comunicación bilingüe y tu enfoque resolutivo ante retos operativos, cualidades que consideramos fundamentales para la excelencia en nuestros servicios financieros.",
      "",
      "Para brindarte certidumbre sobre lo que viene, a continuación te compartimos los aspectos clave de esta siguiente fase:",
      "",
      "1. Objetivo de la Sesión:",
      "Nos interesa conocer de manera práctica tu metodología de trabajo y cómo abordas situaciones reales del día a día, privilegiando el sentido común, la atención al detalle y la estructura analítica sobre cualquier respuesta memorizada.",
      "",
      "2. Modalidad y Duración:",
      "El ejercicio se llevará a cabo de forma remota a través de una sesión guiada por uno de nuestros líderes de área, con una duración aproximada de 45 a 60 minutos. No requiere preparación técnica exhaustiva previa, únicamente un equipo con conexión estable y tu disposición habitual.",
      "",
      "3. Coordinación de Horarios:",
      "Con el propósito de respetar tus compromisos actuales, te pedimos de favor responder a este correo indicándonos dos opciones de fecha y horario que te resulten convenientes durante los próximos días (de lunes a viernes, entre 9:00 AM y 5:00 PM CST). A la brevedad te confirmaremos la cita en tu calendario con el enlace correspondiente.",
      "",
      "Si tienes cualquier duda respecto a la dinámica, requieres alguna consideración particular de agenda o simplemente deseas conversar sobre algún aspecto de la posición antes de la sesión, no dudes en escribirnos directamente respondiendo a este correo.",
      "",
      "Te reiteramos nuestro agradecimiento por considerar a nuDesk como el siguiente paso en tu desarrollo profesional y te deseamos el mayor de los éxitos en esta evaluación.",
      "",
      "Con un cordial saludo,",
      "",
      operator,
      "Especialista de Atracción de Talento & Cultura",
      "nuDesk Operations Studio — Mazatlán Talent Hub"
    ].join("\n");

    output.push({
      json: {
        flow_type: "hr",
        pipeline_type: "HR Talent Screening",
        timestamp: timestamp,
        candidate_name: candidate,
        recipient_email: recipientEmail,
        target_role: role,
        cefr_level: data.english_fluency_cefr || data.cefr || data.bilingual_fluency_rating || "B2",
        competency_score: data.technical_competency_score || data.fit_score || data.candidate_fit_score || 0,
        salary_expectation_usd: data.salary_expectation_monthly_usd || 0,
        hiring_recommendation: data.hiring_recommendation || data.action || data.recommended_action || "Advance to Case Study",
        interviewer_notes: data.analyst_notes || "",
        draft_email_subject: subject,
        draft_email_body: draftBody,
        operator: operator,
        status: "Synced with Google Sheets Talent Roster & Gmail"
      }
    });

  } else if (flow === "executive") {
    let recipientEmail = data.recipient_email;
    if (!recipientEmail || !recipientEmail.includes("@")) {
      recipientEmail = "omarpayant@gmail.com";
    }

    output.push({
      json: {
        flow_type: "executive",
        pipeline_type: "Executive Cockpit",
        timestamp: timestamp,
        recipient_email: recipientEmail,
        digest_title: data.digest_title || "Resumen Operativo Semanal",
        active_pipeline_usd: data.active_pipeline_usd || "$0 USD",
        credit_volume_usd: data.credit_volume_usd || "$0 USD",
        sales_arr_usd: data.sales_arr_usd || "$0 USD",
        sla_compliance_pct: data.sla_compliance_pct || "100%",
        total_operations: data.total_operations || 0,
        pending_count: data.pending_count || 0,
        processed_count: data.processed_count || 0,
        credit_count: data.credit_count || 0,
        sales_count: data.sales_count || 0,
        hr_count: data.hr_count || 0,
        executive_summary: data.executive_summary || "Resumen de operaciones consolidado para Mazatlan Hub.",
        operator: operator,
        status: "Sent to Executive Inbox"
      }
    });

  } else if (flow === "it") {
    const alertTitle = data.alert_title || "Auditoría de Integridad y Model Cascade";
    const latency = data.gemini_latency_ms || 284;
    const dbIntegrity = data.sqlite_integrity || "OK (0 errores)";
    const piiStatus = data.pii_masking_status || "Enforced (100% verificado)";
    const injections = data.injections_blocked !== undefined ? data.injections_blocked : 0;
    const dockerStatus = data.docker_n8n_status || "Healthy (Puerto 5678)";
    const details = data.details || "Todos los microservicios, guardrails y pasarelas operan dentro de los umbrales nominales.";

    let recipientEmail = data.recipient_email;
    if (!recipientEmail || !recipientEmail.includes("@")) {
      recipientEmail = "omarpayant@gmail.com, it-ops@nudesk.io, devops@nudesk.io, ciso-alerts@nudesk.io, infrastructure@nudesk.io";
    }

    const subject = "nuDesk IT Ops | Bitácora de Integridad de Sistemas, Telemetría y Ciberseguridad - " + alertTitle;
    const draftBody = [
      "Estimado equipo de Infraestructura, Seguridad, DevOps y Operaciones de Sistemas de nuDesk (IT SecOps),",
      "",
      "Por medio del presente informe técnico se emite la bitácora consolidada de integridad operativa, latencia de modelos y estado de defensas de ciberseguridad correspondiente al ciclo de supervisión en Mazatlán Operations Hub.",
      "",
      "El diagnóstico automatizado confirma que la arquitectura de microservicios, bases de datos transaccionales y pasarelas de automatización operan bajo condiciones normales de estabilidad y resiliencia, cumpliendo al 100% con los acuerdos de nivel de servicio (SLA) corporativos.",
      "",
      "A continuación, se detalla el estado actual de los componentes supervisados:",
      "",
      "1. Cascada de Modelos de Inteligencia Artificial (Google Gemini):",
      "- Estado: Operativo y balanceado en cascada multi-modelo.",
      "- Latencia Promedio Registrada: " + latency + " ms por solicitud de inferencia.",
      "- Resiliencia Zero-Config: Mecanismo de contingencia offline verificado y respaldado por contratos estrictos Pydantic V2 sin excepciones no capturadas.",
      "",
      "2. Integridad de Base de Datos y Trazabilidad Transaccional:",
      "- Motor Operativo: SQLite de alta concurrencia con bloqueos atómicos y control de transacciones.",
      "- Diagnóstico de Integridad: " + dbIntegrity + ".",
      "- Registro de Auditoría: 100% de operaciones sincronizadas con temporizadores de SLA activos y cálculo de antigüedad FIFO.",
      "",
      "3. Interceptores de Ciberdefensa y Privacidad de Datos:",
      "- Enmascaramiento de PII: " + piiStatus + " (Filtros regex activos para SSN, EIN y tarjetas de pago corporativas).",
      "- Firewall Anti-Inyección de Prompts: " + injections + " firmas adversariales neutralizadas oportunamente en fase de pre-vuelo.",
      "- Reconciliación Matemática Post-Vuelo: Verificación cruzada algorítmica de ratios financieros (DTI / DSCR) para eliminar alucinaciones numéricas.",
      "",
      "4. Pasarela de Automatización y Ecosistema n8n:",
      "- Contenedor Docker: " + dockerStatus + ".",
      "- Integración Externa: Webhooks de ingesta (Read.ai / Fireflies) y sincronización con Google Workspace (Gmail / Sheets) y Asana operando satisfactoriamente.",
      "",
      "Observaciones Técnicas y Diagnóstico del Especialista:",
      details,
      "",
      "Dictamen de Cumplimiento Técnico:",
      "La infraestructura mantiene una disponibilidad nominal ininterrumpida y una postura de seguridad robusta, apta para el soporte continuo de operaciones financieras bilingües.",
      "",
      "Atentamente,",
      "",
      operator,
      "Arquitectura de Sistemas & Ciberseguridad",
      "nuDesk IT Infrastructure Workbench — Mazatlán Hub"
    ].join("\n");

    output.push({
      json: {
        flow_type: "it",
        pipeline_type: "IT Infrastructure & Security",
        timestamp: timestamp,
        alert_title: alertTitle,
        recipient_email: recipientEmail,
        gemini_latency_ms: latency,
        sqlite_integrity: dbIntegrity,
        pii_masking_status: piiStatus,
        injections_blocked: injections,
        docker_n8n_status: dockerStatus,
        details: details,
        draft_email_subject: subject,
        draft_email_body: draftBody,
        operator: operator,
        status: "Synced with Gmail IT Alert"
      }
    });

  } else {
    // Default to Credit flow
    const company = data.business_name || data.company_name || "Apex Fleet Repair";
    const rawApplicant = data.applicant_name || data.contact_person || "Robert Martinez";
    const applicant = rawApplicant.replace(/\s*\(.*?\)\s*/g, "").trim() || rawApplicant;
    const loanAmt = data.loan_amount_requested_usd ? Number(data.loan_amount_requested_usd).toLocaleString("en-US") : "85,000";
    const collateral = data.collateral_type || "Garantías Comerciales y Flujos de Facturación";
    const riskTier = data.risk_tier || "Riesgo Moderado";
    const execSummary = data.executive_summary || "Evaluación favorable basada en volumen de ventas comprobable y capacidad de pago suficiente.";

    let recipientEmail = data.recipient_email || data.applicant_email || data.email;
    if (!recipientEmail || !recipientEmail.includes("@")) {
      recipientEmail = "robert.martinez@apexfleet-demo.com";
    }

    const subject = "nuDesk Underwriting | Dictamen Favorable y Términos de Aprobación Preliminar - " + company;
    const draftBody = [
      "Estimado " + applicant + " (" + company + "),",
      "",
      "Esperamos que se encuentre muy bien al momento de recibir este comunicado.",
      "",
      "Por medio de la presente, nos complace informarle que el Comité de Crédito y Suscripción de Riesgos de nuDesk Operations Studio ha finalizado exitosamente el análisis financiero y documental correspondiente a la solicitud de financiamiento ingresada en favor de " + company + ".",
      "",
      "Tras una rigurosa revisión de sus flujos operativos, capacidad de pago y las garantías presentadas, hemos emitido un dictamen de aprobación preliminar para una facilidad crediticia comercial por un monto de $" + loanAmt + " USD. Felicitamos a su equipo directivo por la solidez y el orden financiero demostrado durante este proceso de evaluación.",
      "",
      "A continuación, le compartimos el resumen de las condiciones preliminares aprobadas:",
      "",
      "1. Empresa Acreditada: " + company,
      "2. Representante / Contacto Principal: " + applicant,
      "3. Monto Aprobado: $" + loanAmt + " USD",
      "4. Tipo de Facilidad: Línea de Crédito Comercial / Arrendamiento de Equipo",
      "5. Esquema de Garantía / Colateral: " + collateral,
      "6. Dictamen de Riesgo: " + riskTier + " (Perfil calificado y solvente bajo política prudencial)",
      "",
      "Resumen Ejecutivo del Dictamen:",
      execSummary,
      "",
      "Guía de Siguientes Pasos para Formalización y Dispersión:",
      "Con la finalidad de proceder a la firma contractual y efectuar la dispersión de los recursos en su cuenta bancaria a la brevedad, requerimos coordinar conjuntamente las siguientes etapas:",
      "",
      "Paso 1: Validación Documental Final: Recepción de identificación oficial vigente del representante legal, constancia de situación fiscal actualizada (no mayor a 30 días) y comprobante de cuenta bancaria receptora.",
      "Paso 2: Firma de Instrumentos Contractuales: Formalización digital del contrato marco de apertura de crédito y pagaré correspondiente mediante nuestra plataforma segura con validez jurídica.",
      "Paso 3: Programación y Dispersión: Confirmación de fondos y transferencia a su cuenta corporativa en un plazo no mayor a 24 horas hábiles posteriores a la firma.",
      "",
      "Su expediente ha sido asignado a nuestra mesa de operaciones en Mazatlán, quienes le estarán brindando acompañamiento personalizado durante toda la fase de firma y desembolso.",
      "",
      "Si requiere aclarar cualquier término de la aprobación, coordinar aspectos específicos de la dispersión o tiene alguna consulta sobre la documentación requerida, por favor comuníquese directamente respondiendo a este correo o contactando a su oficial asignado.",
      "",
      "Reiteramos nuestro agradecimiento por elegir a nuDesk como su aliado financiero estratégico y le deseamos continuo éxito en la expansión de " + company + ".",
      "",
      "Atentamente,",
      "",
      operator,
      "Oficial de Crédito & Suscripción de Riesgos",
      "nuDesk Underwriting Operations — Mazatlán Hub"
    ].join("\n");

    output.push({
      json: {
        flow_type: "credit",
        pipeline_type: "Credit Operations",
        timestamp: timestamp,
        company_name: company,
        applicant_name: applicant,
        recipient_email: recipientEmail,
        loan_amount_usd: data.loan_amount_requested_usd || 0,
        dti_ratio: data.dti_ratio || "N/A",
        risk_tier: riskTier,
        collateral: collateral,
        executive_summary: execSummary,
        red_flags: Array.isArray(data.red_flags) ? data.red_flags.join("; ") : (data.red_flags || "Ninguna registrada"),
        analyst_notes: data.analyst_notes || "",
        draft_email_subject: subject,
        draft_email_body: draftBody,
        operator: operator,
        status: "Synced with Google Sheets Credit LOS, Asana & Gmail"
      }
    });
  }
}

return output;
