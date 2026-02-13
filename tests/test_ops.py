import os
import tempfile
import unittest
from pathlib import Path

from codebasegpt.ai import answer_question_with_metadata
from codebasegpt.indexer import index_repository
from codebasegpt.ops import guardrail_settings, redact_pii


class OpsTests(unittest.TestCase):
    def test_redaction(self) -> None:
        text = "Contact me at a@b.com with card 4242 4242 4242 4242"
        out = redact_pii(text)
        self.assertIn("[REDACTED_EMAIL]", out)
        self.assertIn("[REDACTED_CARD]", out)

    def test_guardrail_settings_env(self) -> None:
        old = os.environ.get("CBG_MIN_CONFIDENCE")
        os.environ["CBG_MIN_CONFIDENCE"] = "0.8"
        try:
            self.assertEqual(guardrail_settings()["min_confidence"], 0.8)
        finally:
            if old is None:
                os.environ.pop("CBG_MIN_CONFIDENCE", None)
            else:
                os.environ["CBG_MIN_CONFIDENCE"] = old

    def test_policy_flags_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / "auth.py").write_text("def auth_login():\n    return True\n", encoding="utf-8")
            db = tmp_path / "graph.sqlite"
            index_repository(repo, db)

            meta = answer_question_with_metadata(db, "possible security breach in login flow")
            self.assertIn("security", meta["policy_flags"])
            self.assertTrue(meta["needs_human"])


if __name__ == "__main__":
    unittest.main()
