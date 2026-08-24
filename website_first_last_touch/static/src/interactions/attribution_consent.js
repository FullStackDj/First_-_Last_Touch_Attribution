import { post } from "@web/core/network/http_service";

let pendingCapture;

export function captureCurrentAttribution() {
    return post("/website/first-last-touch/capture", {
        page: `${window.location.pathname}${window.location.search}`,
        referrer: document.referrer,
        csrf_token: odoo.csrf_token || "",
    });
}

export function captureAttributionAfterConsent() {
    if (pendingCapture) {
        return pendingCapture;
    }
    pendingCapture = new Promise((resolve) => {
        setTimeout(() => {
            const capture = captureCurrentAttribution();
            capture.catch(() => {});
            resolve(capture);
        }, 0);
    });
    return pendingCapture;
}

function captureAfterCookieModalHidden(event) {
    const target = event.target;
    if (!(target instanceof Element) || !target.closest("#website_cookies_bar")) {
        return;
    }
    document.removeEventListener("hidden.bs.modal", captureAfterCookieModalHidden);
    captureAttributionAfterConsent();
}

document.addEventListener(
    "optionalCookiesAccepted",
    captureAttributionAfterConsent,
    { once: true }
);
document.addEventListener("hidden.bs.modal", captureAfterCookieModalHidden);
