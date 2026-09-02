from datetime import datetime

from odoo.tests.common import TransactionCase


class TestAttribution(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls.env["website.first.last.touch.mixin"]
        cls.host = "example.com"
        cls.website_id = 7

    def _snapshot(self, page, referrer="", second=0):
        return self.engine._build_attribution_snapshot(
            page, referrer, self.website_id, self.host,
            observed_at=datetime(2026, 1, 2, 3, 4, second),
        )

    def _state(self, first, latest=False):
        return {"version": 1, "website_id": self.website_id, "host": self.host,
                "first": first, "latest": latest}

    def _merge(self, state, candidate, website_id=None):
        return self.engine._attribution_merge_state(state, candidate, website_id or self.website_id, self.host)

    def test_first_latest_atomic_and_navigation(self):
        direct = self._snapshot("/welcome", second=1)
        state, changed = self._merge(None, direct)
        self.assertTrue(changed)
        self.assertEqual(state["first"]["kind"], "direct")
        self.assertFalse(state["latest"])
        self.assertNotIn("flt_latest_touch_data", self.engine._attribution_values_from_state(state))
        first = self._snapshot("/one?utm_source=google&utm_medium=cpc&utm_campaign=spring", second=2)
        state, _ = self._merge(None, first)
        self.assertIn(
            "flt_latest_touch_data", self.engine._attribution_values_from_state(state)
        )
        partial = self._snapshot("/two?utm_campaign=summer", "https://search.example/result", second=3)
        state, changed = self._merge(state, partial)
        self.assertTrue(changed)
        self.assertEqual(state["first"]["utm"]["source"], "google")
        self.assertEqual(state["latest"]["utm"], {"campaign": "summer"})
        duplicate = self._snapshot("/two?utm_campaign=summer", "https://example.com/two", second=4)
        unchanged, changed = self._merge(state, duplicate)
        self.assertFalse(changed)
        self.assertEqual(unchanged["latest"]["at"], partial["at"])
        changed_landing, changed = self._merge(
            unchanged, self._snapshot("/three?utm_campaign=summer", second=5)
        )
        self.assertTrue(changed)
        self.assertEqual(changed_landing["latest"]["landing_path"], "/three")
        self.assertIsNone(self._snapshot(
            "/next", "https://example.com:443/three?utm_source=internal", second=6
        ))
        referral = self._snapshot(
            "/article?secret=discarded",
            "https://News.Example/path/story?email=private#part", second=7,
        )
        self.assertEqual(referral["referrer"], "https://news.example")
        self.assertEqual(referral["landing_path"], "/article")
        self.assertNotIn("private", str(referral))
        self.assertIsNone(self._snapshot("https://[broken", "https://[broken", second=8))

    def test_utm_click_ids_and_sanitizing(self):
        click_ids = ("gclid", "gbraid", "wbraid", "fbclid", "msclkid")
        for index, name in enumerate(click_ids):
            with self.subTest(name=name):
                snapshot = self._snapshot(
                    f"/ad?utm_term=blue+shoes&utm_content=hero&{name}=Valid_1-2.3~4",
                    second=index,
                )
                self.assertEqual(snapshot["utm"], {
                    "term": "blue shoes", "content": "hero",
                })
                self.assertEqual(snapshot["click_ids"][name], "Valid_1-2.3~4")
                self.assertEqual(snapshot["kind"], "ad_click")
        sanitized = self._snapshot(
            "/ad?utm_source=" + "a" * 300 + "&gclid=bad%0D%0Avalue", second=6
        )
        self.assertEqual(len(sanitized["utm"]["source"]), 100)
        self.assertEqual(sanitized["click_ids"]["gclid"], "badvalue")
        rejected = self._snapshot("/ad?gclid=bad%3Dvalue", second=7)
        self.assertEqual(rejected["kind"], "direct")
        self.assertFalse(rejected["click_ids"])

    def test_signed_state_and_website_isolation(self):
        first = self._snapshot("/?utm_source=newsletter", second=1)
        state = self._state(first)
        token, fitted = self.engine._attribution_sign_state(state)
        self.assertLessEqual(len(token), 3500)
        decoded, invalid = self.engine._attribution_decode_state(
            token, self.website_id, self.host
        )
        self.assertFalse(invalid)
        self.assertEqual(decoded, fitted)
        midpoint = len(token) // 2
        bad_token = token[:midpoint] + ("A" if token[midpoint] != "A" else "B") + token[midpoint + 1:]
        for raw in (bad_token, "x" * 3501, 9):
            decoded, invalid = self.engine._attribution_decode_state(
                raw, self.website_id, self.host
            )
            self.assertIsNone(decoded)
            self.assertTrue(invalid)
        decoded, invalid = self.engine._attribution_decode_state(
            token, self.website_id + 1, self.host
        )
        self.assertIsNone(decoded)
        self.assertTrue(invalid)
        replacement = self._snapshot("/other?utm_source=partner", second=2)
        isolated, changed = self._merge(state, replacement, self.website_id + 1)
        self.assertTrue(changed)
        self.assertEqual(isolated["website_id"], self.website_id + 1)
        self.assertEqual(isolated["first"], replacement)

    def test_models_merge_customer_sale_security_and_native_utm(self):
        first = self._snapshot("/?utm_source=google&utm_campaign=spring", second=1)
        middle = self._snapshot("/?utm_source=bing&utm_campaign=summer", second=2)
        latest = self._snapshot("/?utm_source=partner&utm_campaign=autumn", second=3)
        values_one = self.engine._attribution_values_from_state(self._state(first, middle))
        values_two = self.engine._attribution_values_from_state(self._state(middle, latest))
        source = self.env["utm.source"].create({"name": "Native Source"})
        medium = self.env["utm.medium"].create({"name": "Native Medium"})
        campaign = self.env["utm.campaign"].create({"name": "Native Campaign"})
        lead_one = self.env["crm.lead"].create({
            "name": "First attributed lead", "source_id": source.id,
            "medium_id": medium.id, "campaign_id": campaign.id, **values_one,
        })
        lead_two = self.env["crm.lead"].create({
            "name": "Second attributed lead", **values_two,
        })
        self.assertEqual(
            (lead_one.source_id, lead_one.medium_id, lead_one.campaign_id),
            (source, medium, campaign),
        )
        self.assertEqual(lead_one.flt_first_source, "google")
        self.assertEqual(lead_one.flt_latest_campaign, "summer")
        company = self.env["res.company"].create({"name": "Second Attribution Company"})
        company_lead = self.env["crm.lead"].with_company(company).create(
            {"name": "Other company lead", "company_id": company.id, **values_one})
        self.assertEqual((company_lead.company_id, company_lead.flt_first_source), (company, "google"))
        merged = (lead_one | lead_two)._merge_data([
            "flt_first_touch_data", "flt_latest_touch_data"
        ])
        self.assertEqual(merged["flt_first_touch_data"]["at"], first["at"])
        self.assertEqual(merged["flt_latest_touch_data"]["at"], latest["at"])
        copied = lead_one.copy({"name": "Copied lead"})
        self.assertFalse(copied.flt_first_touch_data or copied.flt_latest_touch_data)
        customer = lead_one._create_customer()
        self.assertEqual(customer.flt_first_touch_data, lead_one.flt_first_touch_data)
        shared = self.env["res.partner"].create({"name": "Existing shared customer"})
        lead_two._handle_partner_assignment(
            force_partner_id=shared.id,
            create_missing=False,
        )
        self.assertEqual(lead_two.partner_id, shared)
        self.assertFalse(shared.flt_first_touch_data)
        quotation_context = lead_one._prepare_opportunity_quotation_context()
        self.assertEqual(quotation_context["default_flt_first_touch_data"], values_one["flt_first_touch_data"])
        quotation = self.env["sale.order"].with_context(quotation_context).create({
            "partner_id": customer.id, "opportunity_id": lead_one.id,
        })
        self.assertEqual(quotation.flt_first_touch_data, lead_one.flt_first_touch_data)
        self.assertEqual(quotation.flt_latest_touch_data, lead_one.flt_latest_touch_data)
        quotation_copy = quotation.copy()
        self.assertFalse(quotation_copy.flt_first_touch_data or quotation_copy.flt_latest_touch_data)
        order = self.env["sale.order"].create({
            "partner_id": customer.id, "opportunity_id": lead_one.id,
            "flt_latest_touch_data": values_two["flt_latest_touch_data"],
        })
        self.assertEqual(order.flt_first_touch_data, lead_one.flt_first_touch_data)
        self.assertEqual(order.flt_latest_touch_data["at"], latest["at"])
        self.assertFalse(order.copy().flt_first_touch_data)
        public_fields = self.env["crm.lead"].with_user(
            self.env.ref("base.public_user")
        ).fields_get(["flt_first_source", "flt_latest_click_id"])
        self.assertFalse(public_fields)
