import json
from urllib.parse import urlsplit

from odoo.tests import tagged
from odoo.tests.common import HttpCase

@tagged("post_install", "-at_install")
class TestAttributionHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)
        cls.website.cookies_bar = True
        cls.cookie_name = f"odoo_flt_{cls.website.id}"

    def _set_consent(self, optional):
        self.opener.cookies["website_cookies_bar"] = json.dumps(
            {"required": True, "optional": optional, "ts": 1}
        )

    def _state(self):
        raw = self.opener.cookies.get(self.cookie_name)
        state, invalid = self.env["website.first.last.touch.mixin"]._attribution_decode_state(
            raw, self.website.id, urlsplit(self.base_url()).hostname,
        )
        self.assertFalse(invalid)
        return state

    def _post_lead(self, name, referrer):
        response = self.url_open(
            "/website/form/crm.lead",
            data={
                "name": name, "contact_name": "Website Visitor",
                "email_from": f"{name.replace(' ', '.').lower()}@example.com",
            },
            headers={"Referer": referrer},
        )
        response.raise_for_status()
        record_id = json.loads(response.text)["id"]
        self.env.invalidate_all()
        return self.env["crm.lead"].browse(record_id)

    def test_capture_internal_navigation_latest_and_withdrawal(self):
        self._set_consent(True)
        first_url = "/?utm_source=google&utm_medium=cpc&utm_campaign=spring&gclid=G_1"
        self.url_open(first_url).raise_for_status()
        first_raw = self.opener.cookies.get(self.cookie_name)
        state = self._state()
        self.assertEqual(state["first"]["utm"]["source"], "google")
        self.assertEqual(state["first"]["click_ids"]["gclid"], "G_1")
        self.url_open("/contactus", headers={
            "Referer": self.base_url() + first_url,
        }).raise_for_status()
        self.assertEqual(self.opener.cookies.get(self.cookie_name), first_raw)
        self.url_open("/contactus?utm_campaign=summer&fbclid=F_2").raise_for_status()
        state = self._state()
        self.assertEqual(state["first"]["utm"]["campaign"], "spring")
        self.assertEqual(state["latest"]["utm"], {"campaign": "summer"})
        self.assertEqual(state["latest"]["click_ids"], {"fbclid": "F_2"})
        self._set_consent(False)
        self.url_open("/contactus").raise_for_status()
        self.assertNotIn(self.cookie_name, self.opener.cookies.get_dict())

    def test_missing_and_declined_consent_do_not_capture(self):
        self.url_open("/?utm_source=missing").raise_for_status()
        self.assertNotIn(self.cookie_name, self.opener.cookies.get_dict())
        self._set_consent(False)
        self.url_open("/?utm_source=declined").raise_for_status()
        self.assertNotIn(self.cookie_name, self.opener.cookies.get_dict())

    def test_same_request_form_needs_no_hidden_fields(self):
        self._set_consent(True)
        referrer = (
            self.base_url()
            + "/contactus?utm_source=linkedin&utm_term=odoo&utm_content=hero&wbraid=W_3"
        )
        lead = self._post_lead("Same Request Attribution", referrer)
        self.assertEqual(
            (lead.flt_first_source, lead.flt_latest_term, lead.flt_latest_content),
            ("linkedin", "odoo", "hero"),
        )
        self.assertEqual((lead.flt_latest_click_id_type, lead.flt_latest_click_id),
                         ("wbraid", "W_3"))
        self.assertEqual(lead.flt_first_landing_path, "/contactus")

    def test_native_utm_continues_to_fill_standard_fields(self):
        self._set_consent(True)
        path = "/contactus?utm_source=NativeSource&utm_medium=NativeMedium&utm_campaign=NativeCampaign"
        self.url_open(path).raise_for_status()
        lead = self._post_lead("Native UTM Lead", self.base_url() + path)
        self.assertEqual(
            (lead.source_id.name, lead.medium_id.name, lead.campaign_id.name),
            ("NativeSource", "NativeMedium", "NativeCampaign"),
        )
        self.assertEqual(lead.flt_latest_source, "NativeSource")

    def test_backend_create_does_not_read_browser_cookie(self):
        self._set_consent(True)
        self.url_open("/?utm_source=browser").raise_for_status()
        lead = self.env["crm.lead"].create({"name": "Manual backend lead"})
        self.assertFalse(lead.flt_first_touch_data or lead.flt_latest_touch_data)
