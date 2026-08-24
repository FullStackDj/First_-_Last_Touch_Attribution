from odoo import http
from odoo.http import request


class WebsiteFirstLastTouchController(http.Controller):

    @http.route(
        "/website/first-last-touch/capture",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        readonly=True,
    )
    def capture(self, page="", referrer="", **kwargs):
        response = request.make_json_response({"ok": True})
        engine = request.env["website.first.last.touch.mixin"]
        engine._attribution_capture_explicit(
            response,
            str(page or "")[:4096],
            str(referrer or "")[:2048],
        )
        return response
