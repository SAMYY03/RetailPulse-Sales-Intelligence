import json
import tempfile
import unittest
from pathlib import Path

import generate_weekly_brief as brief


class WeeklyBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = brief.load_facts(brief.ROOT / "outputs" / "measure-validation.json")

    def test_loads_seven_validated_facts(self):
        self.assertEqual(set(self.facts), set(brief.METRICS))
        self.assertEqual(self.facts["orders"]["display"], "6,273")
        self.assertEqual(self.facts["growth"]["display"], "79.8%")

    def test_sample_passes_and_renders_evidence(self):
        draft = brief.sample_brief()
        brief.validate_brief(draft, self.facts)
        output = brief.render(draft, self.facts, "sample")
        self.assertIn("$895,507.22 [revenue]", output)
        self.assertIn("## Evidence", output)

    def test_rejects_an_invented_number(self):
        draft = brief.sample_brief()
        draft["risks"][0] += " Forecast growth is 25%."
        with self.assertRaisesRegex(ValueError, "unsupported number"):
            brief.validate_brief(draft, self.facts)

    def test_rejects_failed_validation_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "failed.json"
            path.write_text(json.dumps({"checks": 220, "failures": [{}], "results": []}))
            with self.assertRaisesRegex(ValueError, "must pass"):
                brief.load_facts(path)


if __name__ == "__main__":
    unittest.main()
