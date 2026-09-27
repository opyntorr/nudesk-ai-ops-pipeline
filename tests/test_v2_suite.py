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


class TestDeskMateV2Suite(unittest.TestCase):

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
        self.assertIn("--nd-green: #059669", light_css)
        self.assertIn("--nd-bg: #F8FAFC", light_css)

        dark_css = get_nudesk_css("dark")
        self.assertIn("--nd-green: #10B981", dark_css)
        self.assertIn("--nd-bg: #0B0F17", dark_css)

    def test_database_persistence(self):
        database.init_db()
        rec_id = database.save_operation(
            operator_name="Unit Test Operator",
            operator_role="Tester",
            module_type="credit",
            entity_name="Test Enterprise LLC",
            headline_metric="Low Risk | $50k",
            assessment_summary="Viable test profile",
            full_output_json={"test": True}
        )
        self.assertIsInstance(rec_id, int)
        recent = database.get_operations(limit=5)
        self.assertTrue(len(recent) >= 1)
        self.assertEqual(recent[0]["entity_name"], "Test Enterprise LLC")

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


if __name__ == "__main__":
    unittest.main()
