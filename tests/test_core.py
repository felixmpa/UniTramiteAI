import unittest
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

if __name__ == "__main__":
    unittest.main()
