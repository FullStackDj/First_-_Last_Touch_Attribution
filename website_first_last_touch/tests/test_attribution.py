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