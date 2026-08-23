import copy

from odoo import models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "website.first.last.touch.mixin"]

    def website_form_input_filter(self, request, values):
        values = super().website_form_input_filter(request, values)
        engine = self.env["website.first.last.touch.mixin"]
        state = engine._attribution_capture_website_form(request.future_response)
        attribution_values = engine._attribution_values_from_state(state)
        values.update(attribution_values)
        return values

    def _merge_get_fields_specific(self):
        fields_info = super()._merge_get_fields_specific()
        engine = self.env["website.first.last.touch.mixin"]
        fields_info.update({
            "flt_first_touch_data": lambda fname, leads: engine._merge_attribution_snapshots(
                leads.mapped(fname)
            ),
            "flt_latest_touch_data": lambda fname, leads: engine._merge_attribution_snapshots(
                leads.mapped(fname), latest=True
            ),
        })
        return fields_info

    def _create_customer(self, with_parent=None):
        self.ensure_one()
        existing_ids = set(self.partner_id.ids)
        if with_parent:
            existing_ids.update(with_parent.ids)
        partner = super()._create_customer(with_parent=with_parent)
        if partner and partner.id not in existing_ids and not partner.flt_first_touch_data:
            values = self._prepare_partner_attribution()
            if values:
                partner.write(values)
        return partner

    def _prepare_opportunity_quotation_context(self):
        context = super()._prepare_opportunity_quotation_context()
        self.ensure_one()
        for field_name, value in self._prepare_sale_attribution().items():
            context.setdefault(f"default_{field_name}", copy.deepcopy(value))
        return context
