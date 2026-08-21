import binascii
import copy
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit

from odoo import api, fields, models
from odoo.http import request
from odoo.tools.misc import hash_sign, verify_hash_signed


ATTRIBUTION_GROUP = "sales_team.group_sale_salesman"
ATTRIBUTION_VERSION = 1
ATTRIBUTION_COOKIE_SCOPE = "website_first_last_touch.cookie"
ATTRIBUTION_COOKIE_LIMIT = 3500
ATTRIBUTION_KINDS = {"direct", "utm", "ad_click", "referral"}
UTM_PARAMETERS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
)
CLICK_ID_PARAMETERS = (
    "gclid",
    "gbraid",
    "wbraid",
    "fbclid",
    "msclkid",
)
CLICK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._~-]+$")


class WebsiteFirstLastTouchMixin(models.AbstractModel):
    _name = "website.first.last.touch.mixin"
    _description = "Website First and Latest Touch Mixin"

    flt_first_touch_data = fields.Json(
        string="First Touch Data",
        readonly=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_touch_data = fields.Json(
        string="Latest Acquisition Data",
        readonly=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_touch_at = fields.Datetime(
        string="First Touch At",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )

    flt_latest_touch_at = fields.Datetime(
        string="Latest Acquisition At",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_source = fields.Char(
        string="First Source",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        index="btree_not_null",
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_source = fields.Char(
        string="Latest Source",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        index="btree_not_null",
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_medium = fields.Char(
        string="First Medium",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_medium = fields.Char(
        string="Latest Medium",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_campaign = fields.Char(
        string="First Campaign",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_campaign = fields.Char(
        string="Latest Campaign",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        index="btree_not_null",
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_term = fields.Char(
        string="First Term",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_term = fields.Char(
        string="Latest Term",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_content = fields.Char(
        string="First Content",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_content = fields.Char(
        string="Latest Content",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_landing_path = fields.Char(
        string="First Landing Page",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_landing_path = fields.Char(
        string="Latest Acquisition Landing Page",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_referrer = fields.Char(
        string="First External Referrer",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_referrer = fields.Char(
        string="Latest External Referrer",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_click_id_type = fields.Char(
        string="First Click ID Type",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_click_id_type = fields.Char(
        string="Latest Click ID Type",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_first_click_id = fields.Char(
        string="First Click ID",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )
    flt_latest_click_id = fields.Char(
        string="Latest Click ID",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        index="btree_not_null",
        groups=ATTRIBUTION_GROUP,
    )
    flt_has_ad_click_id = fields.Boolean(
        string="Has Ad Click ID",
        compute="_compute_flt_attribution_summary",
        store=True,
        copy=False,
        groups=ATTRIBUTION_GROUP,
    )

    @api.depends("flt_first_touch_data", "flt_latest_touch_data")
    def _compute_flt_attribution_summary(self):
        for record in self:
            first = record._attribution_snapshot_summary(record.flt_first_touch_data)
            latest = record._attribution_snapshot_summary(record.flt_latest_touch_data)
            for prefix, summary in (("first", first), ("latest", latest)):
                setattr(record, f"flt_{prefix}_touch_at", summary["at"])
                setattr(record, f"flt_{prefix}_source", summary["source"])
                setattr(record, f"flt_{prefix}_medium", summary["medium"])
                setattr(record, f"flt_{prefix}_campaign", summary["campaign"])
                setattr(record, f"flt_{prefix}_term", summary["term"])
                setattr(record, f"flt_{prefix}_content", summary["content"])
                setattr(record, f"flt_{prefix}_landing_path", summary["landing_path"])
                setattr(record, f"flt_{prefix}_referrer", summary["referrer"])
                setattr(record, f"flt_{prefix}_click_id_type", summary["click_id_type"])
                setattr(record, f"flt_{prefix}_click_id", summary["click_id"])
            record.flt_has_ad_click_id = bool(first["click_id"] or latest["click_id"])

    @api.model
    def _attribution_snapshot_summary(self, snapshot):
        empty = {
            "at": False,
            "source": False,
            "medium": False,
            "campaign": False,
            "term": False,
            "content": False,
            "landing_path": False,
            "referrer": False,
            "click_id_type": False,
            "click_id": False,
        }
        if not self._attribution_valid_snapshot(snapshot):
            return empty
        utm = snapshot.get("utm") if isinstance(snapshot.get("utm"), dict) else {}
        click_ids = snapshot.get("click_ids") if isinstance(snapshot.get("click_ids"), dict) else {}
        click_type = next((name for name in CLICK_ID_PARAMETERS if click_ids.get(name)), False)
        source = utm.get("source")
        referrer = snapshot.get("referrer")
        if not source and referrer:
            source = self._attribution_normalize_host(self._attribution_urlsplit(referrer).hostname)
        if not source and snapshot.get("kind") == "direct":
            source = "Direct"
        return {
            "at": self._attribution_datetime(snapshot.get("at")),
            "source": source or False,
            "medium": utm.get("medium") or False,
            "campaign": utm.get("campaign") or False,
            "term": utm.get("term") or False,
            "content": utm.get("content") or False,
            "landing_path": snapshot.get("landing_path") or False,
            "referrer": referrer or False,
            "click_id_type": click_type,
            "click_id": click_type and click_ids[click_type] or False,
        }

    @api.model
    def _attribution_parameter_names(self):
        return UTM_PARAMETERS + CLICK_ID_PARAMETERS

    @api.model
    def _get_attribution_cookie_retention(self):
        return 31 * 24 * 60 * 60

    @api.model
    def _get_attribution_cookie_domain(self):
        return None

    @api.model
    def _attribution_cookie_name(self, website):
        return f"odoo_flt_{website.id}"

    @api.model
    def _attribution_truncate_utf8(self, value, limit):
        encoded = value.encode("utf-8")
        if len(encoded) <= limit:
            return value
        return encoded[:limit].decode("utf-8", "ignore")

    @api.model
    def _sanitize_attribution_value(self, name, value):
        if value is None:
            return ""
        value = unicodedata.normalize("NFKC", str(value))
        value = "".join(char for char in value if not unicodedata.category(char).startswith("C"))
        value = re.sub(r"\s+", " ", value).strip()
        if name in CLICK_ID_PARAMETERS:
            value = self._attribution_truncate_utf8(value, 256)
            return value if CLICK_ID_PATTERN.fullmatch(value) else ""
        limits = {
            "utm_source": 100,
            "utm_medium": 100,
            "utm_campaign": 150,
            "utm_term": 150,
            "utm_content": 200,
        }
        return self._attribution_truncate_utf8(value, limits.get(name, 512))

    @api.model
    def _attribution_normalize_host(self, value):
        if not value:
            return ""
        value = str(value).strip()
        if "://" in value:
            target = value
        elif value.count(":") >= 2 and not value.startswith("["):
            target = f"//[{value}]"
        else:
            target = f"//{value}"
        parsed = self._attribution_urlsplit(target)
        host = parsed.hostname or ""
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError:
            return ""
        return host.lower().rstrip(".")[:253]

    @api.model
    def _attribution_urlsplit(self, value):
        try:
            return urlsplit(str(value or ""))
        except (TypeError, ValueError):
            return urlsplit("")

    @api.model
    def _attribution_current_host(self):
        return self._attribution_normalize_host(request.httprequest.host_url)

    @api.model
    def _attribution_normalize_path(self, value, limit=512):
        value = self._sanitize_attribution_value("path", value or "/")
        value = re.sub(r"/{2,}", "/", value)
        if not value.startswith("/"):
            value = f"/{value}"
        return self._attribution_truncate_utf8(value, limit) or "/"

    @api.model
    def _attribution_page_parts(self, page_url, current_host):
        page_url = self._attribution_truncate_utf8(str(page_url or ""), 4096)
        try:
            parsed = urlsplit(page_url)
        except (TypeError, ValueError):
            return "", ""
        if parsed.netloc and self._attribution_normalize_host(parsed.hostname) != current_host:
            return "", ""
        return self._attribution_normalize_path(parsed.path), parsed.query
