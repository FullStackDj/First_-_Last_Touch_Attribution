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