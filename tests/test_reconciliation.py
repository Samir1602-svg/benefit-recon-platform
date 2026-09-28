import unittest

import pandas as pd

from reconciliation import reconcile_benefits, validate_input_frames


def frame(rows):
    return pd.DataFrame(rows)


class ReconciliationTests(unittest.TestCase):
    def test_requires_keys_and_audited_fields_in_both_files(self):
        source = frame({"Plan_ID": ["P1"], "Benefit_Service": ["PCP"]})
        coded = frame({"Plan_ID": ["P1"], "Benefit_Service": ["PCP"], "Copay": ["20"]})

        with self.assertRaisesRegex(ValueError, "Source file must include at least one audited field"):
            validate_input_frames(source, coded)

    def test_reports_rows_missing_from_coded_export(self):
        source = frame({
            "Plan_ID": ["P1", "P1"],
            "Benefit_Service": ["PCP", "Specialist"],
            "Copay": ["$20", "$40"],
        })
        coded = frame({
            "Plan_ID": ["P1"],
            "Benefit_Service": ["PCP"],
            "Copay": ["20"],
        })

        result = reconcile_benefits(source, coded)

        self.assertEqual(result["total_rows"], 2)
        self.assertEqual(result["affected_rows"], 1)
        self.assertEqual(result["accuracy"], 50.0)
        self.assertIn("Benefit row presence", result["errors"]["Field_Audited"].tolist())

    def test_accuracy_is_based_on_affected_rows_not_error_count(self):
        source = frame({
            "Plan_ID": ["P1", "P1"],
            "Benefit_Service": ["PCP", "Specialist"],
            "Copay": ["$20", "$40"],
            "Coinsurance": ["0%", "10%"],
            "Deductible_Applies": ["No", "Yes"],
        })
        coded = frame({
            "Plan_ID": ["P1", "P1"],
            "Benefit_Service": ["PCP", "Specialist"],
            "Copay": ["$25", "$40"],
            "Coinsurance": ["10%", "10%"],
            "Deductible_Applies": ["Yes", "Yes"],
        })

        result = reconcile_benefits(source, coded)

        self.assertEqual(result["type1_errors"], 2)
        self.assertEqual(result["type2_errors"], 1)
        self.assertEqual(result["affected_rows"], 1)
        self.assertEqual(result["accuracy"], 50.0)


if __name__ == "__main__":
    unittest.main()
