"""python3 -m unittest: the rules on single sentences, including the ones that must not fire."""
import json
import unittest

import claimcheck as cc

LEAD = {"id": "a", "first_name": "Lena", "company": "Kranwerk GmbH", "title": "Head of Sales Development",
        "headline": "Head of Sales Development | Kranwerk GmbH", "employees": 240.0, "employee_range": "201-500",
        "sales_team": 12.0, "months_in_role": 30, "years_in_role": 2, "new_in_role": False,
        "company_growth_6m_pct": 18, "company_growth_1y_pct": 25,
        "summary": "Building outbound teams across 7 countries.", "company_description": "Kranwerk builds pricing software."}
OTHER = {**LEAD, "id": "b", "first_name": "Jonas", "company": "Lumora GmbH"}


def kinds(text, lead=LEAD, icp="Ask: a 15-minute call."):
    agent = {"icp": icp, "leads": [{"id": lead["id"], "message": text}]}
    return [f[3] for f in cc.check_agent([lead, OTHER], agent)]


class Numbers(unittest.TestCase):
    def test_grounded_numbers_pass(self):
        self.assertEqual(kinds("Kranwerk grew 18% in the last 6 months and your 12-person SDR team is busy."), [])
        self.assertEqual(kinds("With about 250 employees and 7 countries to cover, is a 15-minute call worth it?"), [])

    def test_number_used_as_the_wrong_field(self):
        self.assertEqual(kinds("Your 18-person SDR team is busy."), ["misattributed_number"])

    def test_number_lifted_from_profile_text(self):
        self.assertEqual(kinds("Kranwerk grew 7% this year."), ["number_from_text"])

    def test_invented_number(self):
        self.assertEqual(kinds("Your 40 reps are busy."), ["invented_number"])

    def test_hedge_only_widens_the_employee_count(self):
        self.assertEqual(kinds("With 250 employees, lists pile up."), ["invented_number"])


class Claims(unittest.TestCase):
    def test_new_role(self):
        self.assertEqual(kinds("Congrats on the new role."), ["false_new_role"])
        self.assertEqual(kinds("You moved into the role 3 months ago.", {**LEAD, "months_in_role": 3, "new_in_role": True}), [])

    def test_growth_direction(self):
        shrinking = {**LEAD, "company_growth_6m_pct": -9, "company_growth_1y_pct": -4}
        self.assertEqual(kinds("With Kranwerk growing fast, lists pile up.", shrinking), ["wrong_growth_direction"])
        self.assertEqual(kinds("With Kranwerk growing fast, lists pile up."), [])

    def test_offer_talk_is_not_a_growth_claim(self):
        shrinking = {**LEAD, "company_growth_6m_pct": -9, "company_growth_1y_pct": -4}
        self.assertEqual(kinds("Evaboot can help your SDRs grow pipeline.", shrinking), [])

    def test_events_need_a_field(self):
        self.assertEqual(kinds("Saw you just raised a Series B."), ["unsupported_event"])
        self.assertEqual(kinds("Congrats on the launch.", {**LEAD, "company_description": "Kranwerk launched v2."}), [])

    def test_function(self):
        self.assertEqual(kinds("As you lead the marketing team, lists land on you."), ["wrong_function"])
        self.assertEqual(kinds("Your SDR team spends hours on lists."), [])

    def test_leak_from_another_lead(self):
        self.assertEqual(kinds("Worth a call to see if it fits Lumora?"), ["cross_lead_leak"])
        self.assertEqual(kinds("Hi Jonas, worth a call?"), ["cross_lead_leak"])


class Judge(unittest.TestCase):
    def test_judge_parses_and_flags(self):
        reply = 'Here you go: {"claims": [{"claim": "grew 7%", "label": "contradicted", "fields": ["company_growth_6m_pct"], "why": "18"}]}'
        out = cc.judge([LEAD], {"leads": [{"id": "a", "message": "Kranwerk grew 7%."}]}, ask=lambda s, u: reply)
        self.assertEqual(out["leads"]["a"][0]["label"], "contradicted")

    def test_judge_bad_json_counts_as_a_flag(self):
        out = cc.judge([LEAD], {"leads": [{"id": "a", "message": "Hi"}]}, ask=lambda s, u: "no json")
        self.assertEqual(out["leads"]["a"][0]["label"], "error")

    def test_judge_never_sees_email_or_id(self):
        seen = []
        cc.judge([{**LEAD, "email": "lena@kranwerk.example"}], {"leads": [{"id": "a", "message": "Hi"}]},
                 ask=lambda s, u: seen.append(json.loads(u)) or '{"claims": []}')
        self.assertNotIn("email", seen[0]["lead"])
        self.assertNotIn("id", seen[0]["lead"])


class Kappa(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(cc.kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)
        self.assertAlmostEqual(cc.kappa([1, 1, 0, 0], [1, 0, 1, 0]), 0.0)


if __name__ == "__main__":
    unittest.main()
