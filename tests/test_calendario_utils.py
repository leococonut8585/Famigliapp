import unittest
from collections import defaultdict
from app.calendario import utils as calendario_utils

# Minimal mock for config.USERS if needed by the functions being tested
# For get_specialized_schedule_violations, users_config is passed in, so direct mocking might not be needed
# unless other utils called by it depend on a global config.USERS.
# For now, we'll assume it's self-contained or users_config is sufficient.

class TestCalendarioUtilsSpecializedViolations(unittest.TestCase):

    def test_get_specialized_schedule_violations(self):
        sample_events_base = [
            # Shifts
            {"date": "2023-01-01", "category": "shift", "employee": "sara"},
            {"date": "2023-01-01", "category": "shift", "employee": "maya"},
            {"date": "2023-01-02", "category": "shift", "employee": "jun"},
            {"date": "2023-01-03", "category": "shift", "employee": "ken"},
            {"date": "2023-01-04", "category": "shift", "employee": "sara"},
            # Specialized Events
            {"id": 1, "date": "2023-01-01", "title": "マミーイベント1", "category": "マミー系"},
            {"id": 2, "date": "2023-01-02", "title": "タトゥーイベント1", "category": "タトゥー"},
            {"id": 3, "date": "2023-01-03", "title": "マミーイベント2", "category": "マミー系"},
            {"id": 4, "date": "2023-01-04", "title": "通常イベント", "category": "other"}, # No rule
            {"id": 5, "date": "2023-01-05", "title": "マミーイベント3無人", "category": "マミー系"}, # No one on shift
        ]

        sample_rules_base = {
            "specialized_requirements": {
                "マミー系": ["sara", "hitomi"],
                "タトゥー": ["jun"]
            }
            # "specialized_requirements_translation_map": { # Assuming direct keys for now
            #     "マミー系": "マミー系",
            #     "タトゥー": "タトゥー"
            # }
        }

        mock_users_config = { # Simplified, only if needed by the function signature (it is)
            "sara": {"name": "Sara"}, "hitomi": {"name": "Hitomi"},
            "jun": {"name": "Jun"}, "ken": {"name": "Ken"}, "maya": {"name": "Maya"}
        }

        # Test Case 1: No violation for マミー系 (sara is on shift)
        events_case1 = [e for e in sample_events_base if e['date'] == "2023-01-01" or e['id'] == 1]
        violations = calendario_utils.get_specialized_schedule_violations(events_case1, sample_rules_base, mock_users_config)
        self.assertEqual(len(violations), 0, "Test Case 1 Failed: Should be no violation for マミー系 with sara on shift.")

        # Test Case 2: Violation for マミー系 (neither sara nor hitomi on shift, only ken)
        events_case2 = [
            {"date": "2023-01-03", "category": "shift", "employee": "ken"}, # Ken is on shift
            {"id": 3, "date": "2023-01-03", "title": "マミーイベント2", "category": "マミー系"},
        ]
        violations = calendario_utils.get_specialized_schedule_violations(events_case2, sample_rules_base, mock_users_config)
        self.assertEqual(len(violations), 1, "Test Case 2 Failed: Should be one violation.")
        expected_msg_2 = "マミー系の予定がある日(2023-01-03)に、指定担当者 (sara, hitomi) のいずれも割り当てられていません。"
        self.assertIn(expected_msg_2, violations, "Test Case 2 Failed: Violation message mismatch.")

        # Test Case 3: No relevant specialized events
        events_case3 = [
            {"date": "2023-01-01", "category": "shift", "employee": "sara"},
            {"id": 4, "date": "2023-01-04", "title": "通常イベント", "category": "other"},
        ]
        violations = calendario_utils.get_specialized_schedule_violations(events_case3, sample_rules_base, mock_users_config)
        self.assertEqual(len(violations), 0, "Test Case 3 Failed: No specialized events, should be no violations.")

        # Test Case 4: Event exists but no rule for its category
        events_case4 = [
            {"date": "2023-01-01", "category": "shift", "employee": "sara"},
            {"id": 1, "date": "2023-01-01", "title": "マミーイベント1", "category": "マミー系"},
        ]
        rules_case4 = {"specialized_requirements": {"タトゥー": ["jun"]}} # No rule for マミー系
        violations = calendario_utils.get_specialized_schedule_violations(events_case4, rules_case4, mock_users_config)
        self.assertEqual(len(violations), 0, "Test Case 4 Failed: Event category not in rules, should be no violation.")

        # Test Case 5: Staff on shift but not the designated one for that genre
        # マミー系 requires sara or hitomi. jun is on shift for タトゥー event. This is fine.
        # Let's test a マミー系 event where 'jun' is on shift, but 'sara'/'hitomi' are required.
        events_case5 = [
            {"date": "2023-01-02", "category": "shift", "employee": "jun"}, # Jun is on shift
            {"id": 1, "date": "2023-01-02", "title": "マミーイベント強制", "category": "マミー系"}, # マミー系 event
        ]
        violations = calendario_utils.get_specialized_schedule_violations(events_case5, sample_rules_base, mock_users_config)
        self.assertEqual(len(violations), 1, "Test Case 5 Failed: Jun is on shift, but not designated for マミー系.")
        expected_msg_5 = "マミー系の予定がある日(2023-01-02)に、指定担当者 (sara, hitomi) のいずれも割り当てられていません。"
        self.assertIn(expected_msg_5, violations, "Test Case 5 Failed: Violation message mismatch.")

        # Test Case 6: No one on shift for a specialized event day
        events_case6 = [
             # No shifts on 2023-01-05
            {"id": 5, "date": "2023-01-05", "title": "マミーイベント3無人", "category": "マミー系"},
        ]
        violations = calendario_utils.get_specialized_schedule_violations(events_case6, sample_rules_base, mock_users_config)
        self.assertEqual(len(violations), 1, "Test Case 6 Failed: No one on shift for a マミー系 event.")
        expected_msg_6 = "マミー系の予定がある日(2023-01-05)に、指定担当者 (sara, hitomi) のいずれも割り当てられていません。"
        self.assertIn(expected_msg_6, violations, "Test Case 6 Failed: Violation message mismatch.")

        # Test Case 7: Rule exists, but the list of designated staff is empty
        events_case7 = [
            {"date": "2023-01-01", "category": "shift", "employee": "sara"},
            {"id": 1, "date": "2023-01-01", "title": "マミーイベント1", "category": "マミー系"},
        ]
        rules_case7 = {"specialized_requirements": {"マミー系": []}} # Empty designated list
        violations = calendario_utils.get_specialized_schedule_violations(events_case7, rules_case7, mock_users_config)
        self.assertEqual(len(violations), 0, "Test Case 7 Failed: Empty designated staff list should not cause violation.")

        # Test Case 8: Specialized requirements empty in rules
        rules_case8 = {"specialized_requirements": {}}
        violations = calendario_utils.get_specialized_schedule_violations(sample_events_base, rules_case8, mock_users_config)
        self.assertEqual(len(violations), 0, "Test Case 8 Failed: Empty specialized_requirements object should lead to no violations.")

        # Test Case 9: Rule value is not a list (should be handled gracefully)
        events_case9 = sample_events_base
        rules_case9 = {"specialized_requirements": {"マミー系": "sara"}} # "sara" instead of ["sara"]
        # Expecting it to print a warning and skip this rule, not crash.
        violations = calendario_utils.get_specialized_schedule_violations(events_case9, rules_case9, mock_users_config)
        # Depending on how it's handled: if it skips, events requiring "マミー系" might show violations or not.
        # The current implementation of get_specialized_schedule_violations prints a warning and skips.
        # So, "マミー系" events will effectively have no valid rule and thus no violations from this malformed rule.
        # Let's verify no violation *due to this malformed rule*.
        # If "sara" was on shift for event on 2023-01-01, it would be 0.
        # If "ken" was on shift for event on 2023-01-03, it would also be 0 because the rule for マミー系 is skipped.

        # Let's check specific event on 2023-01-03 (マミーイベント2) where ken is on shift.
        # If the rule was `{"マミー系": ["sara", "hitomi"]}`, this would be a violation.
        # Since the rule `{"マミー系": "sara"}` is skipped, there's no *valid* rule for マミー系.
        # Therefore, no violation should be reported for マミー系 events.
        test_event_for_case9 = [e for e in events_case9 if e['id'] == 3 or (e['date'] == '2023-01-03' and e['category'] == 'shift')]
        violations_for_case9_event3 = calendario_utils.get_specialized_schedule_violations(test_event_for_case9, rules_case9, mock_users_config)
        self.assertEqual(len(violations_for_case9_event3), 0, "Test Case 9 Failed: Malformed rule should be skipped, resulting in no violation for that category.")


if __name__ == '__main__':
    unittest.main()
