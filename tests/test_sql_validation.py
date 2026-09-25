import unittest

from lib.sql_validation import validate_sql_query


class SQLValidationTests(unittest.TestCase):
    def test_accepts_simple_select(self):
        ok, error = validate_sql_query("SELECT * FROM sales LIMIT 10", "SELECT")
        self.assertTrue(ok)
        self.assertEqual(error, "")

    def test_rejects_multiple_statements(self):
        ok, error = validate_sql_query("SELECT 1; SELECT 2", "SELECT")
        self.assertFalse(ok)
        self.assertIn("Multiple SQL statements", error)

    def test_rejects_privilege_management(self):
        ok, error = validate_sql_query("GRANT SELECT ON TABLE sales TO analysts", "SELECT")
        self.assertFalse(ok)
        self.assertIn("blocked", error)

    def test_rejects_mismatched_declared_type(self):
        ok, error = validate_sql_query("DELETE FROM sales WHERE id = 1", "SELECT")
        self.assertFalse(ok)
        self.assertIn("does not match", error)


if __name__ == "__main__":
    unittest.main()
