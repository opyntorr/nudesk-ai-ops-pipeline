import unittest
import os
import json

from models import CreditTriageOutput, SalesLeadOutput, HRTalentOutput
from mock_data import MOCK_FALLBACK_CREDIT, MOCK_FALLBACK_SALES, MOCK_FALLBACK_HR
import database
import auth_rbac
import meeting_queue
import document_reader


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


if __name__ == "__main__":
    unittest.main()
