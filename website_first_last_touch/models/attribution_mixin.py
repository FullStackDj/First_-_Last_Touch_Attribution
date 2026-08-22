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

    @api.model
    def _attribution_referrer(self, referrer, current_host):
        referrer = self._attribution_truncate_utf8(str(referrer or ""), 2048)
        if not referrer:
            return "", False
        parsed = self._attribution_urlsplit(referrer)
        host = self._attribution_normalize_host(parsed.hostname)
        if parsed.scheme not in ("http", "https") or not host:
            return "", False
        if host == current_host:
            return "", True
        return f"{parsed.scheme}://{host}", False

    @api.model
    def _attribution_query_values(self, query):
        values = {}
        try:
            pairs = parse_qsl(query, keep_blank_values=False, max_num_fields=50)
        except ValueError:
            return values
        allowed = set(self._attribution_parameter_names())
        for name, value in pairs:
            if name in allowed and name not in values:
                sanitized = self._sanitize_attribution_value(name, value)
                if sanitized:
                    values[name] = sanitized
        return values

    @api.model
    def _attribution_compact_snapshot(self, snapshot, aggressive=False):
        snapshot = copy.deepcopy(snapshot)
        size = len(json.dumps(snapshot, ensure_ascii=True))
        if size <= 1400 and not aggressive:
            return snapshot
        utm = snapshot.get("utm", {})
        for key in tuple(utm):
            if aggressive:
                limit = 40 if key in ("source", "medium") else 56
            else:
                limit = 72 if key in ("source", "medium") else 96
            utm[key] = self._attribution_truncate_utf8(utm[key], limit)
        click_ids = snapshot.get("click_ids", {})
        primary = next((name for name in CLICK_ID_PARAMETERS if click_ids.get(name)), None)
        if aggressive:
            snapshot["click_ids"] = {primary: click_ids[primary]} if primary else {}
        landing_limit = 64 if aggressive else 180
        snapshot["landing_path"] = self._attribution_truncate_utf8(
            snapshot.get("landing_path", "/"), landing_limit
        )
        if len(json.dumps(snapshot, ensure_ascii=True)) > 1400:
            utm.pop("content", None)
        if len(json.dumps(snapshot, ensure_ascii=True)) > 1400:
            utm.pop("term", None)
        if len(json.dumps(snapshot, ensure_ascii=True)) > 1400 and primary:
            snapshot["click_ids"] = {primary: click_ids[primary]}
        if aggressive and len(json.dumps(snapshot, ensure_ascii=True)) > 1100:
            utm.pop("content", None)
        if aggressive and len(json.dumps(snapshot, ensure_ascii=True)) > 1100:
            utm.pop("term", None)
        return snapshot

    @api.model
    def _build_attribution_snapshot(self, page_url, referrer, website_id, current_host, observed_at=None):
        landing_path, query = self._attribution_page_parts(page_url, current_host)
        if not landing_path:
            return None
        values = self._attribution_query_values(query)
        utm = {
            name.removeprefix("utm_"): values[name]
            for name in UTM_PARAMETERS
            if values.get(name)
        }
        click_ids = {
            name: values[name]
            for name in CLICK_ID_PARAMETERS
            if values.get(name)
        }
        external_referrer, internal_referrer = self._attribution_referrer(referrer, current_host)
        if not utm and not click_ids and not external_referrer and internal_referrer:
            return None
        kind = "ad_click" if click_ids else "utm" if utm else "referral" if external_referrer else "direct"
        snapshot = {
            "at": fields.Datetime.to_string(observed_at or fields.Datetime.now()),
            "kind": kind,
            "landing_path": landing_path,
            "referrer": external_referrer,
            "utm": utm,
            "click_ids": click_ids,
        }
        return self._attribution_compact_snapshot(snapshot)

    @api.model
    def _is_qualified_attribution_touch(self, snapshot):
        return isinstance(snapshot, dict) and snapshot.get("kind") in ATTRIBUTION_KINDS - {"direct"}

    @api.model
    def _attribution_fingerprint(self, snapshot):
        if not isinstance(snapshot, dict):
            return ""
        has_marketing_parameters = bool(snapshot.get("utm") or snapshot.get("click_ids"))
        data = {
            "kind": snapshot.get("kind"),
            "landing_path": snapshot.get("landing_path"),
            "referrer": False if has_marketing_parameters else snapshot.get("referrer"),
            "utm": snapshot.get("utm"),
            "click_ids": snapshot.get("click_ids"),
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @api.model
    def _should_update_last_touch(self, current_snapshot, candidate):
        return (
            self._is_qualified_attribution_touch(candidate)
            and self._attribution_fingerprint(current_snapshot)
            != self._attribution_fingerprint(candidate)
        )

    @api.model
    def _attribution_datetime(self, value):
        try:
            return fields.Datetime.to_datetime(value) if value else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _attribution_valid_snapshot(self, snapshot):
        if not isinstance(snapshot, dict) or snapshot.get("kind") not in ATTRIBUTION_KINDS:
            return False
        if not isinstance(snapshot.get("at"), str) or not self._attribution_datetime(snapshot["at"]):
            return False
        if not isinstance(snapshot.get("landing_path"), str) or len(snapshot["landing_path"]) > 512:
            return False
        if not isinstance(snapshot.get("referrer", ""), str) or len(snapshot.get("referrer", "")) > 512:
            return False
        utm = snapshot.get("utm", {})
        click_ids = snapshot.get("click_ids", {})
        if not isinstance(utm, dict) or not isinstance(click_ids, dict):
            return False
        if set(utm) - {name.removeprefix("utm_") for name in UTM_PARAMETERS}:
            return False
        if set(click_ids) - set(CLICK_ID_PARAMETERS):
            return False
        return all(isinstance(value, str) and len(value) <= 512 for value in utm.values()) and all(
            isinstance(value, str) and len(value) <= 256 for value in click_ids.values()
        )

    @api.model
    def _attribution_valid_state(self, state, website_id, current_host):
        return bool(
            isinstance(state, dict)
            and state.get("version") == ATTRIBUTION_VERSION
            and state.get("website_id") == website_id
            and state.get("host") == current_host
            and self._attribution_valid_snapshot(state.get("first"))
            and (not state.get("latest") or self._attribution_valid_snapshot(state.get("latest")))
        )

    @api.model
    def _attribution_merge_state(self, state, candidate, website_id, current_host):
        if not self._attribution_valid_state(state, website_id, current_host):
            state = {
                "version": ATTRIBUTION_VERSION,
                "website_id": website_id,
                "host": current_host,
                "first": False,
                "latest": False,
            }
        else:
            state = copy.deepcopy(state)
        if not candidate:
            return state if state.get("first") else None, False
        if not state.get("first"):
            state["first"] = candidate
            return state, True
        current_latest = state.get("latest") or state["first"]
        if self._should_update_last_touch(current_latest, candidate):
            state["latest"] = candidate
            return state, True
        return state, False

    @api.model
    def _attribution_sign_state(self, state):
        retention = self._get_attribution_cookie_retention()
        token = hash_sign(
            self.env(su=True),
            ATTRIBUTION_COOKIE_SCOPE,
            state,
            expiration=timedelta(seconds=retention),
        )
        if len(token) <= ATTRIBUTION_COOKIE_LIMIT:
            return token, state
        compact = copy.deepcopy(state)
        compact["first"] = self._attribution_compact_snapshot(compact["first"], aggressive=True)
        if compact.get("latest"):
            compact["latest"] = self._attribution_compact_snapshot(compact["latest"], aggressive=True)
        token = hash_sign(
            self.env(su=True),
            ATTRIBUTION_COOKIE_SCOPE,
            compact,
            expiration=timedelta(seconds=retention),
        )
        return (token, compact) if len(token) <= ATTRIBUTION_COOKIE_LIMIT else (None, None)

    @api.model
    def _attribution_decode_state(self, raw, website_id, current_host):
        if not raw:
            return None, False
        if not isinstance(raw, str) or len(raw) > ATTRIBUTION_COOKIE_LIMIT:
            return None, True
        try:
            state = verify_hash_signed(self.env(su=True), ATTRIBUTION_COOKIE_SCOPE, raw)
        except (ValueError, TypeError, UnicodeError, binascii.Error, json.JSONDecodeError):
            return None, True
        if not self._attribution_valid_state(state, website_id, current_host):
            return None, True
        return state, False

    @api.model
    def _attribution_read_state(self, website, current_host):
        return self._attribution_decode_state(
            request.cookies.get(self._attribution_cookie_name(website)),
            website.id,
            current_host,
        )

    @api.model
    def _attribution_delete_cookie(self, response, website):
        response.set_cookie(
            self._attribution_cookie_name(website),
            "",
            max_age=0,
            expires=0,
            path="/",
            domain=self._get_attribution_cookie_domain(),
            secure=bool(request.httprequest.is_secure),
            httponly=True,
            samesite="Lax",
            cookie_type="required",
        )

    @api.model
    def _attribution_write_cookie(self, response, website, state):
        token, fitted_state = self._attribution_sign_state(state)
        if not token:
            self._attribution_delete_cookie(response, website)
            return None
        retention = self._get_attribution_cookie_retention()
        response.set_cookie(
            self._attribution_cookie_name(website),
            token,
            max_age=retention,
            expires=datetime.now(timezone.utc) + timedelta(seconds=retention),
            path="/",
            domain=self._get_attribution_cookie_domain(),
            secure=bool(request.httprequest.is_secure),
            httponly=True,
            samesite="Lax",
            cookie_type="optional",
        )
        return fitted_state

    @api.model
    def _attribution_optional_cookies_allowed(self):
        try:
            return bool(request.env["ir.http"]._is_allowed_cookie("optional"))
        except (TypeError, ValueError):
            return False

    @api.model
    def _attribution_capture(self, response, page_url, referrer):
        website = request.website
        cookie_name = self._attribution_cookie_name(website)
        if not self._attribution_optional_cookies_allowed():
            if request.cookies.get(cookie_name):
                self._attribution_delete_cookie(response, website)
            return None
        current_host = self._attribution_current_host()
        if not current_host:
            return None
        state, invalid = self._attribution_read_state(website, current_host)
        candidate = self._build_attribution_snapshot(page_url, referrer, website.id, current_host)
        state, changed = self._attribution_merge_state(state, candidate, website.id, current_host)
        if state and (changed or invalid):
            state = self._attribution_write_cookie(response, website, state)
        elif invalid:
            self._attribution_delete_cookie(response, website)
        return state

    @api.model
    def _attribution_capture_explicit(self, response, page_url, referrer):
        return self._attribution_capture(response, page_url, referrer)

    @api.model
    def _attribution_capture_website_form(self, response):
        cache_key = "website_first_last_touch.form_state"
        if cache_key in request.httprequest.environ:
            return request.httprequest.environ[cache_key]
        page_url = request.httprequest.url
        referrer = request.httprequest.referrer or ""
        current_host = self._attribution_current_host()
        has_query_touch = any(name in request.httprequest.args for name in self._attribution_parameter_names())
        referrer_host = self._attribution_normalize_host(self._attribution_urlsplit(referrer).hostname)
        if not has_query_touch and referrer and referrer_host == current_host:
            page_url = referrer
            referrer = ""
        state = self._attribution_capture(response, page_url, referrer)
        request.httprequest.environ[cache_key] = state
        return state

    @api.model
    def _attribution_capture_eligible(self, response):
        return bool(
            getattr(request, "is_frontend", False)
            and request.httprequest.method == "GET"
            and getattr(response, "status_code", 0) == 200
            and getattr(response, "mimetype", "") == "text/html"
            and not request.httprequest.path.startswith(("/web/", "/website/first-last-touch/capture"))
        )

    @api.model
    def _attribution_process_response(self, response):
        if not getattr(request, "is_frontend", False) or not hasattr(request, "website"):
            return None
        website = request.website
        if not self._attribution_optional_cookies_allowed():
            if request.cookies.get(self._attribution_cookie_name(website)):
                self._attribution_delete_cookie(response, website)
            return None
        if not self._attribution_capture_eligible(response):
            return None
        return self._attribution_capture(
            response,
            request.httprequest.url,
            request.httprequest.referrer or "",
        )

    @api.model
    def _attribution_expand_snapshot(self, snapshot, state):
        if not self._attribution_valid_snapshot(snapshot):
            return False
        result = copy.deepcopy(snapshot)
        result.update({
            "version": ATTRIBUTION_VERSION,
            "website_id": state["website_id"],
            "host": state["host"],
        })
        return result

    @api.model
    def _attribution_values_from_state(self, state):
        if not isinstance(state, dict) or not state.get("first"):
            return {}
        first = self._attribution_expand_snapshot(state["first"], state)
        latest_source = state.get("latest")
        if not latest_source and self._is_qualified_attribution_touch(state["first"]):
            latest_source = state["first"]
        latest = self._attribution_expand_snapshot(latest_source, state) if latest_source else False
        if not first:
            return {}
        values = {"flt_first_touch_data": first}
        if latest:
            values["flt_latest_touch_data"] = latest
        return values

    def _prepare_partner_attribution(self):
        self.ensure_one()
        return {
            "flt_first_touch_data": copy.deepcopy(self.flt_first_touch_data),
            "flt_latest_touch_data": copy.deepcopy(self.flt_latest_touch_data),
        } if self.flt_first_touch_data else {}

    def _prepare_sale_attribution(self):
        self.ensure_one()
        return self._prepare_partner_attribution()

    @api.model
    def _merge_attribution_snapshots(self, snapshots, latest=False):
        valid = [
            snapshot
            for snapshot in snapshots
            if self._attribution_valid_snapshot(snapshot)
            and (not latest or self._is_qualified_attribution_touch(snapshot))
        ]
        if not valid:
            return False
        return copy.deepcopy(
            max(valid, key=lambda item: self._attribution_datetime(item["at"]))
            if latest
            else min(valid, key=lambda item: self._attribution_datetime(item["at"]))
        )
