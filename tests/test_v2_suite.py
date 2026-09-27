import unittest
import os
import json

from models import CreditTriageOutput, SalesLeadOutput, HRTalentOutput
from mock_data import MOCK_FALLBACK_CREDIT, MOCK_FALLBACK_SALES, MOCK_FALLBACK_HR
import database
import auth_rbac
import meeting_queue
import document_reader
from styles.nudesk_theme import get_nudesk_css
from streamlit.testing.v1 import AppTest


class TestNuDeskOpsV2Suite(unittest.TestCase):

    def test_pydantic_models(self):
        # Credit
        self.assertEqual(MOCK_FALLBACK_CREDIT.applicant_name, "Robert Martinez")
        self.assertIn(MOCK_FALLBACK_CREDIT.risk_tier, ["Low Risk", "Moderate Risk", "High Risk"])

        # Sales
        self.assertEqual(MOCK_FALLBACK_SALES.company_name, "Sunbelt Logistics LLC")
        self.assertTrue(1 <= MOCK_FALLBACK_SALES.lead_score <= 100)

        # HR
        self.assertEqual(MOCK_FALLBACK_HR.candidate_name, "Sofia Valdez")
        self.assertTrue(1 <= MOCK_FALLBACK_HR.overall_fit_score <= 100)
        self.assertEqual(MOCK_FALLBACK_HR.candidate_fit_tier, "High Fit")
        self.assertTrue(1 <= MOCK_FALLBACK_HR.candidate_fit_score <= 100)
        self.assertTrue(0 <= MOCK_FALLBACK_HR.psychometrics_score <= 100)
        self.assertTrue(0 <= MOCK_FALLBACK_HR.knowledge_test_score <= 100)
        self.assertEqual(MOCK_FALLBACK_HR.application_area, "Credit Underwriting & Risk")
        self.assertIn(MOCK_FALLBACK_HR.bilingual_fluency_rating, [
            "C2 Native / Bilingual",
            "C1 Advanced Professional",
            "B2 Working Proficiency",
            "Below Target"
        ])

    def test_auth_rbac(self):
        underwriter = auth_rbac.get_persona_by_role("underwriter")
        self.assertEqual(underwriter.role_key, "underwriter")
        self.assertFalse(underwriter.permissions["it_admin_settings"])

        it_admin = auth_rbac.get_persona_by_role("it_admin")
        self.assertEqual(it_admin.role_key, "it_admin")
        self.assertTrue(it_admin.permissions["it_admin_settings"])

    def test_google_auth_url_generation(self):
        url = auth_rbac.get_google_auth_url(
            client_id="test_client_id_123",
            redirect_uri="http://localhost:8501"
        )
        self.assertTrue(url.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
        self.assertIn("client_id=test_client_id_123", url)
        self.assertIn("redirect_uri=http%3A%2F%2Flocalhost%3A8501", url)
        self.assertIn("response_type=code", url)
        self.assertIn("openid+email+profile", url)

    def test_create_persona_from_google_user(self):
        # Test admin mapping
        admin_data = {
            "name": "Christian Omar Payán Torróntegui",
            "email": "omarpayant@gmail.com",
            "picture": "https://example.com/avatar.png"
        }
        admin_persona = auth_rbac.create_persona_from_google_user(admin_data)
        self.assertEqual(admin_persona.role_key, "it_admin")
        self.assertTrue(admin_persona.permissions["it_admin_settings"])
        self.assertEqual(admin_persona.avatar_initials, "CO")
        self.assertTrue(admin_persona.is_live_google_session)

        # Test standard employee mapping
        user_data = {
            "name": "Elena Smith",
            "email": "elena.smith@clientcorp.com",
            "picture": ""
        }
        user_persona = auth_rbac.create_persona_from_google_user(user_data)
        self.assertEqual(user_persona.role_key, "underwriter")
        self.assertFalse(user_persona.permissions["it_admin_settings"])
        self.assertEqual(user_persona.avatar_initials, "ES")

    def test_theme_css_generation(self):
        light_css = get_nudesk_css("light")
        self.assertIn("--nd-green: #3EA258", light_css)
        self.assertIn("--nd-bg: #F4F7F9", light_css)

        dark_css = get_nudesk_css("dark")
        self.assertIn("--nd-green: #54D67D", dark_css)
        self.assertIn("--nd-bg: #2C3844", dark_css)

    def test_database_persistence(self):
        database.init_db()
        rec_id = database.save_operation(
            operator_name="Unit Test Operator",
            operator_role="Tester",
            module_type="credit",
            entity_name="Benchmark Enterprise LLC",
            headline_metric="Low Risk | $50k",
            assessment_summary="Viable test profile",
            full_output_json={"test": True},
            is_processed=1,
            analyst_notes="Special equipment lien verified"
        )
        self.assertIsInstance(rec_id, int)
        recent = database.get_filtered_operations(module_filter="credit", search_query="Benchmark Enterprise", time_window="all")
        self.assertTrue(len(recent) >= 1)
        self.assertEqual(recent[0]["entity_name"], "Benchmark Enterprise LLC")
        self.assertEqual(recent[0]["analyst_notes"], "Special equipment lien verified")
        # Clean up test record so it never leaks into production UI
        conn = database.get_connection()
        conn.cursor().execute("DELETE FROM operations_history WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()

    def test_sla_and_queue_advancement(self):
        sla_recent = database.calculate_sla_status("2026-09-26 21:00:00", is_processed=0)
        self.assertIn("tier", sla_recent)
        self.assertIn(sla_recent["tier"], ["NEW", "ATTENTION", "BREACH"])

        sla_synced = database.calculate_sla_status("2026-09-26 15:00:00", is_processed=1)
        self.assertEqual(sla_synced["tier"], "SYNCED")
        self.assertEqual(sla_synced["color"], "badge-green")

        next_pending = database.get_next_pending_operation("credit")
        self.assertIsNotNone(next_pending)
        self.assertEqual(next_pending["is_processed"], 0)

    def test_meeting_queue(self):
        self.assertTrue(len(meeting_queue.INCOMING_MEETINGS_QUEUE) >= 3)
        credit_items = meeting_queue.get_queue_items_for_role("underwriter")
        self.assertTrue(all(item["type"] == "credit" for item in credit_items))

    def test_document_reader_url_safety(self):
        # Test handling of empty or invalid URL gracefully without exception
        res = document_reader.extract_text_from_url("")
        self.assertEqual(res, "")
        
        res_invalid = document_reader.extract_text_from_url("https://invalid-non-existent-domain-12345.org")
        self.assertTrue("Unable to scrape" in res_invalid or res_invalid == "")

    def test_streamlit_app_execution(self):
        # End-to-end headless run of app.py to guarantee no runtime NameError or crash
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        at = AppTest.from_file(app_path, default_timeout=10)
        at.run()
        self.assertFalse(at.exception, f"app.py raised unhandled runtime exception: {at.exception}")

    def test_n8n_integration_and_ingestion(self):
        # 1. Test ingestion into queue with active SLA
        rec_id = database.ingest_pending_record(
            module_type="credit",
            entity_name="CI Test Transports LLC",
            headline_metric="$95,000 USD | Working Capital",
            transcript_text="[00:00:01] Underwriter: CI automated intake test transcript.",
            source_channel="Google Drive Intake"
        )
        self.assertIsInstance(rec_id, int)
        
        # Verify retrieved transcript from dynamic record
        import app
        transcript, url, note = app.get_transcript_for_entity(
            "CI Test Transports LLC", "credit", json.dumps({"transcript": "Custom Ingested Transcript Content"})
        )
        self.assertEqual(transcript, "Custom Ingested Transcript Content")

        # 2. Test crm_dispatcher simulation fallback
        import crm_dispatcher
        ok, msg, payload = crm_dispatcher.dispatch_to_n8n("", {"test": True}, flow_type="sales")
        self.assertTrue(ok)
        self.assertIn("Simulation Mode Active", msg)
        self.assertEqual(payload["flow_type"], "sales")

    def test_no_deprecated_streamlit_attributes(self):
        # QA Test: Guarantee zero occurrences of deprecated use_container_width in app.py
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("use_container_width", content, "app.py contains deprecated use_container_width attribute")

    def test_streamlit_server_config(self):
        # QA Test: Guarantee enableCORS=true in .streamlit/config.toml to prevent cross-origin warnings
        cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "config.toml"))
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("enableCORS = true", content, "config.toml must have enableCORS = true")
        self.assertIn("enableXsrfProtection = true", content, "config.toml must have enableXsrfProtection = true")

    def test_synthetic_fixtures_validity(self):
        # QA Test: Validate all synthetic fixtures and generator extraction
        from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
        for provider, module in [("readai", "credit"), ("fireflies", "sales"), ("gdrive", "credit"), ("readai", "hr")]:
            p = generate_synthetic_payload(provider, module)
            self.assertTrue(bool(p), f"Fixture for {provider}/{module} could not be loaded")
            f = extract_ingestion_fields(p, provider, module)
            self.assertIn(f["module_type"], ["credit", "sales", "hr"])
            self.assertTrue(len(f["entity_name"]) > 0)
            self.assertTrue(len(f["transcript_text"]) > 0)

    def test_hr_talent_qualitative_parameters(self):
        # QA Test: Validate HR model handles qualitative fit, psychometrics, and knowledge test
        sample_hr = HRTalentOutput(
            candidate_name="Lucia Beltran",
            applied_role="Risk Analyst",
            application_area="Credit Underwriting & Risk",
            candidate_fit_tier="Moderate Fit",
            candidate_fit_score=79,
            psychometrics_score=82,
            knowledge_test_score=78,
            executive_summary="Competent candidate with moderate credit experience.",
            technical_competencies=["Financial Analysis", "Cash Flow Modeling"],
            behavioral_red_flags=[],
            recommended_action="Hold for Alternate Pipeline",
            next_interview_focus_questions=["Explain your DSCR calculation method."]
        )
        self.assertEqual(sample_hr.candidate_fit_tier, "Moderate Fit")
        self.assertEqual(sample_hr.candidate_fit_score, 79)
        self.assertEqual(sample_hr.psychometrics_score, 82)
        self.assertEqual(sample_hr.knowledge_test_score, 78)
        self.assertEqual(sample_hr.application_area, "Credit Underwriting & Risk")

    def test_hr_candidate_area_inference_and_filtering(self):
        # QA Test: Validate area extraction and inference from database records
        database.init_db()
        hr_records = database.get_filtered_operations(module_filter="hr", time_window="all")
        self.assertTrue(len(hr_records) >= 3, "Expected at least 3 HR records in test database")

        areas = set()
        for r in hr_records:
            area = database.get_candidate_area(r)
            self.assertIn(area, [
                "Credit Underwriting & Risk",
                "Commercial Sales & BDR",
                "Operations & Accounting",
                "Technology & Systems"
            ])
            areas.add(area)

        # Confirm multiple functional areas are represented
        self.assertTrue(len(areas) >= 2, "Expected diverse functional application areas in HR records")

    def test_processed_leads_colored_kpis_and_dual_donuts(self):
        # QA Test: Verify app.py contains KPI cards in processed tabs and dual donut charts
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Check dual donut column definitions across department tabs
        self.assertIn("col_c_donut_status, col_c_donut_risk", code)
        self.assertIn("col_s_donut_status, col_s_donut_tier", code)
        self.assertIn("col_h_donut_status, col_h_donut_fit", code)

        # Check processed audit tabs use colored KPI boxes and exec-log-card
        self.assertIn("hq_area_filter", code)
        self.assertIn("hp_area_filter", code)
        self.assertIn("kpi-large-grid", code)
        self.assertIn("kpi-box-large", code)

    def test_processed_cards_direct_click_hitboxes_and_no_expander(self):
        # QA Test: Validate removal of Details & Assessment expander and presence of direct click hitboxes
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Guarantee 'Details & Assessment' expander is completely removed from processed queue tabs
        credit_processed_section = code.split("with credit_queue_tabs[1]:")[1].split("with col_c_canvas:")[0]
        sales_processed_section = code.split("with sales_queue_tabs[1]:")[1].split("with col_s_canvas:")[0]
        hr_processed_section = code.split("with hr_queue_tabs[1]:")[1].split("with col_h_canvas:")[0]

        self.assertNotIn("Details & Assessment", credit_processed_section, "Credit processed queue should not contain Details & Assessment expander")
        self.assertNotIn("Details & Assessment", sales_processed_section, "Sales processed queue should not contain Details & Assessment expander")
        self.assertNotIn("Details & Assessment", hr_processed_section, "HR processed queue should not contain Details & Assessment expander")

        # Verify transparent overlay buttons for processed cards in Credit, Sales, and HR
        self.assertIn("btn_cp_select_", code, "app.py must contain btn_cp_select_ for credit processed cards")
        self.assertIn("btn_sp_select_", code, "app.py must contain btn_sp_select_ for sales processed cards")
        self.assertIn("btn_hp_select_", code, "app.py must contain btn_hp_select_ for hr processed cards")

        # Verify CSS styling has overlays and hitboxes in nudesk_theme.py
        theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "styles", "nudesk_theme.py"))
        with open(theme_path, "r", encoding="utf-8") as f:
            theme_css = f.read()
        self.assertIn("st-key-btn_cp_select_", theme_css)
        self.assertIn("st-key-btn_sp_select_", theme_css)
        self.assertIn("st-key-btn_hp_select_", theme_css)
        self.assertIn(".exec-card-hitbox", theme_css)
        self.assertIn(".exec-log-card.active", theme_css)

    def test_canvas_dual_mode_processed_dossier_vs_pending(self):
        # QA Test: Verify decision canvas renders historical dossier when processed card is selected
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Verify dual-mode condition checks in Credit, Sales, and HR canvases
        self.assertIn("is_processed_c = (active_credit_rec is not None and active_credit_rec.get(\"is_processed\") == 1)", code)
        self.assertIn("is_processed_s = (active_sales_rec is not None and active_sales_rec.get(\"is_processed\") == 1)", code)
        self.assertIn("is_processed_h = (active_hr_rec is not None and active_hr_rec.get(\"is_processed\") == 1)", code)

        # Verify return-to-pending buttons exist in processed canvas mode
        self.assertIn("btn_c_return_pending", code)
        self.assertIn("btn_s_return_pending", code)
        self.assertIn("btn_h_return_pending", code)

        # Verify archived transcript expanders exist for auditing historical records
        self.assertIn("Archived Call Transcript & Supporting Records", code)
        self.assertIn("Archived Sales Interaction & Notes", code)
        self.assertIn("Archived Candidate Interview Transcript & CV Notes", code)

    def test_database_processed_records_integrity(self):
        # QA Test: Verify database retrieval of processed operations across modules
        database.init_db()
        for mod in ["credit", "sales", "hr"]:
            records = database.get_filtered_operations(module_filter=mod, status_filter="processed", time_window="all")
            self.assertTrue(len(records) >= 1, f"Expected at least 1 processed record for module {mod}")
            for r in records:
                self.assertEqual(r["is_processed"], 1)
                self.assertTrue(bool(r["entity_name"]))
                self.assertTrue(bool(r["headline_metric"]))
                self.assertTrue(bool(r["assessment_summary"]))

    def test_dark_mode_palette_contrast_and_transparent_charts(self):
        # QA Test: Validate lighter slate palette, button text contrast, and transparent charts
        dark_css = get_nudesk_css("dark")
        # 1. Slate palette matched directly from nuDesk footer tokens
        self.assertIn("--nd-bg: #2C3844", dark_css)
        self.assertIn("--nd-surface: #364554", dark_css)
        self.assertIn("--nd-surface-alt: #3F5062", dark_css)
        self.assertIn("--nd-border: #576169", dark_css)

        # 2. Universal secondary buttons: surface background, high contrast, no white blocks
        self.assertIn('button[data-testid="stBaseButton-secondary"]', dark_css)
        self.assertIn("background-color: var(--nd-surface) !important", dark_css)
        self.assertIn("color: var(--nd-text) !important", dark_css)

        # 3. Popover hitboxes: full 100% surface area clickable
        self.assertIn('div[data-testid="stPopover"] button', dark_css)
        self.assertIn('div[data-testid="stPopover"] button *', dark_css)
        self.assertIn('pointer-events: none !important', dark_css)
        self.assertIn('min-height: 42px !important', dark_css)

        # 4. Transparent charts in Vega/Altair CSS
        self.assertIn('.vega-embed', dark_css)
        self.assertIn('background: transparent !important', dark_css)

        # 5. configure_altair_donut helper
        import altair as alt
        import pandas as pd
        from styles.nudesk_theme import configure_altair_donut

        df = pd.DataFrame({"Category": ["A", "B"], "Value": [10, 20]})
        base_chart = alt.Chart(df).mark_arc().encode(theta="Value", color="Category").properties(height=110)
        styled_chart_dark = configure_altair_donut(base_chart, theme="dark")
        chart_dict_dark = styled_chart_dark.to_dict()
        self.assertEqual(chart_dict_dark.get("background"), "transparent")
        self.assertEqual(chart_dict_dark.get("config", {}).get("legend", {}).get("labelColor"), "#F8FAFC")

        styled_chart_light = configure_altair_donut(base_chart, theme="light")
        chart_dict_light = styled_chart_light.to_dict()
        self.assertEqual(chart_dict_light.get("background"), "transparent")
        self.assertEqual(chart_dict_light.get("config", {}).get("legend", {}).get("labelColor"), "#1D242E")

        # 6. Verify app.py renders all charts with theme=None and configure_altair_donut
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("from styles.nudesk_theme import get_nudesk_css, configure_altair_donut", code)
        self.assertEqual(code.count("theme=None"), 8)
        self.assertIn("c_status_chart = configure_altair_donut(c_status_chart", code)
        self.assertIn("c_chart = configure_altair_donut(c_chart", code)
        self.assertIn("s_status_chart = configure_altair_donut(s_status_chart", code)
        self.assertIn("s_chart = configure_altair_donut(s_chart", code)
        self.assertIn("h_status_chart = configure_altair_donut(h_status_chart", code)
        self.assertIn("h_fit_chart = configure_altair_donut(h_fit_chart", code)
        self.assertIn("dept_chart = configure_altair_donut(dept_chart", code)
        self.assertIn("risk_chart = configure_altair_donut(risk_chart", code)

    def test_it_database_explorer_and_query_workbench(self):
        # QA Test: Validate database statistics, schema inspection, safe querying, and vacuum
        database.init_db()
        stats = database.get_database_stats()
        self.assertIn("total_records", stats)
        self.assertIn("credit_count", stats)
        self.assertIn("sales_count", stats)
        self.assertIn("hr_count", stats)
        self.assertIn("processed_count", stats)
        self.assertIn("pending_count", stats)
        self.assertIn("file_size_kb", stats)
        self.assertTrue(stats["total_records"] >= 1)

        schema = database.get_database_schema("operations_history")
        col_names = [col["name"] for col in schema]
        self.assertIn("id", col_names)
        self.assertIn("module_type", col_names)
        self.assertIn("entity_name", col_names)
        self.assertIn("is_processed", col_names)
        self.assertIn("timestamp", col_names)

        # Safe read query execution
        cols, rows, err = database.execute_safe_query("SELECT id, module_type, entity_name FROM operations_history LIMIT 5;")
        self.assertIsNone(err)
        self.assertEqual(cols, ["id", "module_type", "entity_name"])
        self.assertTrue(len(rows) >= 1)

        # Mutating queries must be strictly blocked for security
        cols_b, rows_b, err_b = database.execute_safe_query("DROP TABLE operations_history;")
        self.assertIsNotNone(err_b)
        self.assertIn("Security Policy Violation", err_b)

        # VACUUM optimization
        vac_res = database.vacuum_database()
        self.assertIn("size_before_bytes", vac_res)
        self.assertIn("size_after_bytes", vac_res)

    def test_it_model_cascade_controls_and_ping(self):
        # QA Test: Validate AI engine candidate models, dynamic cascade update, and connectivity test
        import ai_engine
        self.assertTrue(len(ai_engine.AVAILABLE_MODELS) >= 4)
        original_models = ai_engine.get_candidate_models()
        self.assertTrue(len(original_models) >= 1)

        # Test dynamic reordering
        custom_sequence = ["gemini-3.5-flash", "gemini-1.5-pro", "gemini-3.5-flash-lite"]
        ai_engine.set_candidate_models(custom_sequence)
        self.assertEqual(ai_engine.get_candidate_models(), custom_sequence)

        # Test model ping / latency probe (operates safely in demo mode or live if API key present)
        ping_res = ai_engine.test_model_connectivity("gemini-3.5-flash")
        self.assertIn("model", ping_res)
        self.assertIn("status", ping_res)
        self.assertIn("latency_ms", ping_res)
        self.assertIn("connected", ping_res)
        self.assertTrue(ping_res["latency_ms"] >= 0)

        # Restore original cascade
        ai_engine.set_candidate_models(original_models)

    def test_auto_selection_on_queue_tab_switch_and_no_deskmate_references(self):
        # QA Test: Verify on_change tab callbacks exist in app.py and no 'DeskMate' references in key modules
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()

        # Check tab callback keys and on_change bindings
        self.assertIn("key=\"credit_queue_tab_key\"", app_code)
        self.assertIn("on_change=on_credit_tab_change", app_code)
        self.assertIn("key=\"sales_queue_tab_key\"", app_code)
        self.assertIn("on_change=on_sales_tab_change", app_code)
        self.assertIn("key=\"hr_queue_tab_key\"", app_code)
        self.assertIn("on_change=on_hr_tab_change", app_code)

        # Check canvas auto-alignment blocks
        self.assertIn("active_c_tab = st.session_state.get(\"credit_queue_tab_key\"", app_code)
        self.assertIn("active_s_tab = st.session_state.get(\"sales_queue_tab_key\"", app_code)
        self.assertIn("active_h_tab = st.session_state.get(\"hr_queue_tab_key\"", app_code)

        # Check IT tab enhanced sections
        self.assertIn("AI Model Cascade & Governance", app_code)
        self.assertIn("Database Explorer & SQL Workbench", app_code)
        self.assertIn("btn_apply_cascade", app_code)
        self.assertIn("btn_execute_sql", app_code)

        # Zero "DeskMate" or "Deskmate" in operational files
        files_to_check = [
            os.path.join(os.path.dirname(__file__), "..", "app.py"),
            os.path.join(os.path.dirname(__file__), "..", "auth_rbac.py"),
            os.path.join(os.path.dirname(__file__), "..", "crm_dispatcher.py"),
            os.path.join(os.path.dirname(__file__), "..", "README.md"),
            os.path.join(os.path.dirname(__file__), "..", "Makefile")
        ]
        for fpath in files_to_check:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("deskmate", content.lower(), f"File {os.path.basename(fpath)} should not contain 'DeskMate'")

    def test_dark_mode_text_contrast_and_lightened_typography(self):
        # QA Test: Validate lightened typography, input placeholders, table contrast and WCAG AAA compliance
        dark_css = get_nudesk_css("dark")

        # 1. High contrast text tokens in dark mode
        self.assertIn("--nd-text: #FFFFFF", dark_css)
        self.assertIn("--nd-muted: #D1DCE5", dark_css)
        self.assertIn("--nd-green: #54D67D", dark_css)
        self.assertIn("--nd-teal: #4AE0D0", dark_css)

        # 2. Header subtitle lightened for readability
        self.assertIn("color: #E2E8F0 !important;", dark_css)

        # 3. Input placeholder contrast rules
        self.assertIn(".stTextInput input::placeholder", dark_css)
        self.assertIn("color: var(--nd-muted) !important;", dark_css)

        # 4. Table and DataFrame text legibility
        self.assertIn('div[data-testid="stDataFrame"]', dark_css)

        # 5. Badge text tokens lightened
        self.assertIn("#86EFAC", dark_css)  # green badge text
        self.assertIn("#99F6E4", dark_css)  # teal badge text
        self.assertIn("#F1F5F9", dark_css)  # navy badge text
        self.assertIn("#FCA5A5", dark_css)  # red badge text
        self.assertIn("#FDE047", dark_css)  # amber badge text

        # 6. Verify mathematical WCAG contrast ratio >= 7:1 (AAA) against #2C3844 and #364554
        def lum(r, g, b):
            a = []
            for v in [r, g, b]:
                v = v / 255.0
                a.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
            return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

        def contrast(c1_hex, c2_hex):
            c1 = tuple(int(c1_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            c2 = tuple(int(c2_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            l1, l2 = lum(*c1), lum(*c2)
            return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

        # Primary text (#FFFFFF) contrast on body (#2C3844) and surface (#364554)
        self.assertGreaterEqual(contrast("#FFFFFF", "#2C3844"), 7.0)
        self.assertGreaterEqual(contrast("#FFFFFF", "#364554"), 7.0)

        # Muted text (#D1DCE5) contrast on body (#2C3844) and surface (#364554)
        self.assertGreaterEqual(contrast("#D1DCE5", "#2C3844"), 7.0)
        self.assertGreaterEqual(contrast("#D1DCE5", "#364554"), 7.0)

        # 7. Check that app.py uses var(--nd-green) in HR recommendation
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()
        self.assertIn("color:var(--nd-green);\">{hr_out.recommended_action}</div>", app_code)


# Backwards compatibility alias
TestDeskMateV2Suite = TestNuDeskOpsV2Suite

if __name__ == "__main__":
    unittest.main()



