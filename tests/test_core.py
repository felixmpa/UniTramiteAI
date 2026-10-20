import os
import tempfile
import unittest
from pathlib import Path
import core
from core import get_student, validate_request, validate_ticket_format

class TestCore(unittest.TestCase):
    def test_student_exists(self):
        self.assertIsNotNone(get_student("2024-1001"))

    def test_record_requires_active_and_clearance(self):
        student = get_student("2024-1002")
        result = validate_request(student, "Récord académico")
        self.assertTrue(result["matrícula activa"])
        self.assertFalse(result["paz y salvo"])

    def test_certificate_requires_active_enrollment(self):
        student = get_student("2023-2040")
        result = validate_request(student, "Certificación de estudio")
        self.assertFalse(result["matrícula activa"])

    def test_ticket_format(self):
        self.assertTrue(validate_ticket_format("UT-000123"))
        self.assertFalse(validate_ticket_format("ticket123"))

class TestChatSavesRequests(unittest.TestCase):
    """Runs on a temporary SQLite file."""
    def setUp(self):
        self.original_url = os.environ.pop("DATABASE_URL", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = core.DB_PATH
        core.DB_PATH = Path(self.tmp.name) / "test.db"
        core.init_db()
        self.state = {"pending_type": None, "pending_student": None}

    def tearDown(self):
        core.DB_PATH = self.original_db
        self.tmp.cleanup()
        if self.original_url:
            os.environ["DATABASE_URL"] = self.original_url

    def saved(self):
        return [r for r in core.list_requests() if r["Ticket"] != "UT-000001"]

    def test_type_then_student_id(self):
        core.handle_message("Necesito un récord académico", self.state)
        reply = core.handle_message("2024-1001", self.state)
        self.assertIn("UT-000002", reply)
        self.assertEqual(self.saved()[0]["Estado"], "Recibida")

    def test_type_and_student_id_in_same_message(self):
        core.handle_message("Necesito un récord académico, mi matrícula es 2024-1002", self.state)
        rows = self.saved()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Matrícula"], "2024-1002")
        self.assertEqual(rows[0]["Estado"], "Pendiente de revisión")

    def test_student_id_then_type(self):
        core.handle_message("2024-1001", self.state)
        core.handle_message("certificación de estudio", self.state)
        self.assertEqual(self.saved()[0]["Trámite"], "Certificación de estudio")

    def test_student_id_with_status_keyword(self):
        core.handle_message("Quiero una certificación de estudio", self.state)
        core.handle_message("mi matrícula es 2024-1001 para la solicitud", self.state)
        self.assertEqual(len(self.saved()), 1)

    def test_unknown_student_is_not_saved(self):
        reply = core.handle_message("récord para 9999-0000", self.state)
        self.assertIn("no existe", reply)
        self.assertEqual(self.saved(), [])

    def test_ticket_lookup(self):
        self.assertIn("UT-000001", core.handle_message("estado de UT-000001", self.state))

@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "define TEST_DATABASE_URL para probar con PostgreSQL")
class TestChatSavesRequestsPostgres(TestChatSavesRequests):
    """Same scenarios on PostgreSQL. WARNING: drops the requests table of TEST_DATABASE_URL."""
    def setUp(self):
        self.original_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
        core.run("DROP TABLE IF EXISTS requests")
        core.run("DROP SEQUENCE IF EXISTS request_number_seq")
        core.init_db()
        self.state = {"pending_type": None, "pending_student": None}

    def tearDown(self):
        if self.original_url:
            os.environ["DATABASE_URL"] = self.original_url
        else:
            os.environ.pop("DATABASE_URL", None)

if __name__ == "__main__":
    unittest.main()
