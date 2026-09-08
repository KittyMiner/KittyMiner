import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "issue_idempotency.py"
spec = importlib.util.spec_from_file_location("issue_idempotency", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

IntegrityError = module.IntegrityError
plan_actions = module.plan_actions

PAYLOAD = [
    {"issue_id": "GAIA-SAC-FAT-001", "title": "Title 1"},
    {"issue_id": "GAIA-SAC-FAT-002", "title": "Title 2"},
    {"issue_id": "GAIA-SAC-FAT-003", "title": "Title 3"},
]


class IdempotencyPlanningTests(unittest.TestCase):
    def test_first_run_creates_every_absent_canonical_id(self):
        actions = plan_actions(PAYLOAD, [])
        self.assertEqual(
            [a["action"] for a in actions],
            ["CREATE", "CREATE", "CREATE"],
        )

    def test_second_run_skips_every_existing_canonical_id(self):
        existing = [
            {"number": 101, "title": "Title 1", "body": "<!-- gaia-canonical-issue-id:GAIA-SAC-FAT-001 -->"},
            {"number": 102, "title": "Title 2", "body": "<!-- gaia-canonical-issue-id:GAIA-SAC-FAT-002 -->"},
            {"number": 103, "title": "Title 3", "body": "<!-- gaia-canonical-issue-id:GAIA-SAC-FAT-003 -->"},
        ]
        actions = plan_actions(PAYLOAD, existing)
        self.assertEqual(
            [a["action"] for a in actions],
            ["SKIP", "SKIP", "SKIP"],
        )
        self.assertEqual(
            [a["issue_number"] for a in actions],
            [101, 102, 103],
        )

    def test_title_collision_without_marker_fails_closed(self):
        existing = [{"number": 50, "title": "Title 1", "body": "legacy body"}]
        with self.assertRaises(IntegrityError):
            plan_actions(PAYLOAD, existing)

    def test_duplicate_payload_id_fails_closed(self):
        duplicated = PAYLOAD + [
            {"issue_id": "GAIA-SAC-FAT-001", "title": "Other"}
        ]
        with self.assertRaises(IntegrityError):
            plan_actions(duplicated, [])


if __name__ == "__main__":
    unittest.main()
