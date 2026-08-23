import copy

from odoo import api, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "website.first.last.touch.mixin"]

    def copy(self, default=None):
        context = dict(self.env.context)
        context.pop("default_flt_first_touch_data", None)
        context.pop("default_flt_latest_touch_data", None)
        return super(SaleOrder, self.with_context(context)).copy(default)

    @api.model_create_multi
    def create(self, vals_list):
        engine = self.env["website.first.last.touch.mixin"]
        prepared_vals = []
        for original_vals in vals_list:
            vals = dict(original_vals)
            opportunity = self.env["crm.lead"].browse(vals.get("opportunity_id")).exists()
            has_attribution = any(
                field_name in vals
                for field_name in ("flt_first_touch_data", "flt_latest_touch_data")
            )
            if opportunity and has_attribution:
                source_values = opportunity._prepare_sale_attribution()
                if source_values.get("flt_first_touch_data") and not vals.get("flt_first_touch_data"):
                    vals["flt_first_touch_data"] = copy.deepcopy(source_values["flt_first_touch_data"])
                latest = engine._merge_attribution_snapshots(
                    [
                        vals.get("flt_latest_touch_data"),
                        source_values.get("flt_latest_touch_data"),
                    ],
                    latest=True,
                )
                if latest:
                    vals["flt_latest_touch_data"] = latest
            prepared_vals.append(vals)
        return super().create(prepared_vals)
