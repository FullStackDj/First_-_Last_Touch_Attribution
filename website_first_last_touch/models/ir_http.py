from odoo import models
from odoo.http import Response, request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        response = Response.load(response)
        request.env["website.first.last.touch.mixin"]._attribution_process_response(response)
