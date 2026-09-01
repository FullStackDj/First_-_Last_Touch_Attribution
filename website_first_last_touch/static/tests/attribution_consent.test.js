import { expect, test } from "@odoo/hoot";
import { mockFetch } from "@odoo/hoot-mock";

import {
    captureAttributionAfterConsent,
    captureCurrentAttribution,
} from "@website_first_last_touch/interactions/attribution_consent";

function expectCaptureRequest(route, { body, method }) {
    expect(route).toBe("/website/first-last-touch/capture");
    expect(method).toBe("POST");
    expect(body.get("page")).toBe(`${window.location.pathname}${window.location.search}`);
    expect(body.get("referrer")).toBe(document.referrer);
    expect(body.get("csrf_token")).toBe(odoo.csrf_token || "");
    return new Response("{}", { status: 200 });
}

test("current acquisition page is posted", async () => {
    mockFetch(expectCaptureRequest);
    await captureCurrentAttribution();
});

test("optional cookie consent posts the current acquisition page", async () => {
    mockFetch(expectCaptureRequest);
    await captureAttributionAfterConsent();
});
