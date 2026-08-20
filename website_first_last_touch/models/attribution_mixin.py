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