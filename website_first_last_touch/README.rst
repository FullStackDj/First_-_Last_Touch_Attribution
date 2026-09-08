First & Last Touch Attribution for Odoo
=======================================

.. image:: static/description/readme_banner.png
   :alt: First and Last Touch Attribution preserves the real acquisition source from Website to CRM and Sales.
   :align: center
   :width: 100%

.. image:: static/description/readme_feature_strip.png
   :alt: Full journey tracking, Direct return protection, consent-aware attribution, and validated behavior.
   :align: center
   :width: 100%

Never lose the marketing source behind a customer.

A prospect may first arrive from Google Ads, return later through Direct traffic,
and convert only after another campaign. First & Last Touch Attribution keeps
the acquisition story clear instead of letting the final visit hide the source
that actually brought the prospect.

The module preserves one stable First Touch and one Latest Qualified Acquisition
with UTM data, landing page, external referrer, supported advertising click IDs,
and timestamps. That context follows the normal Odoo flow from Website forms to
CRM, a newly created customer, and quotations or Sales Orders created from the
Opportunity. No external attribution SaaS or mandatory API is required.

Documentation
-------------

Detailed documentation is included in the ``doc`` folder:

* `Complete User and Administrator Guide <doc/1.%20Complete%20User%20and%20Administrator%20Guide.pdf>`_
  — installation, attribution concepts, daily use, consent behavior, CRM and
  Sales workflow, troubleshooting, and administration.
* `Technical Architecture and Operations Guide <doc/2.%20Technical%20Architecture%20and%20Operations%20Guide.pdf>`_
  — Website capture, signed first-party state, consent lifecycle, attribution
  rules, CRM merge behavior, customer and Sales propagation, security, and
  operational details.
* `Testing, Acceptance, and Go-Live Guide <doc/3.%20Testing%20Acceptance%20and%20Go-Live%20Guide.pdf>`_
  — automated checks, browser validation, acceptance scenarios, regression
  coverage, rollout, and go-live verification.

The guides are written for business users, administrators, implementation
specialists, and technical support teams. They provide the step-by-step detail
needed to understand, operate, validate, and support the module independently.

Full Technical Implementation and Testing Report
------------------------------------------------

The complete case study explains the standard Odoo UTM, Website Form, CRM,
customer, Sales, and cookie-consent architecture used by the module. It covers
First Touch and Latest Qualified Acquisition rules, atomic snapshots, click-ID
handling, signed browser state, multi-Website protection, CRM merge behavior,
customer and Sales propagation, copy safety, access control, and final
validation.

The completed QA includes 27 functional and technical scenarios, 139 deep
server-side assertions, nine Python/HttpCase tests, two Hoot JavaScript tests,
and a real browser end-to-end flow from optional-cookie consent to signed
attribution state, standard Website form submission, and the expected CRM
acquisition.

`Read the Full Technical Implementation and Testing Report on Google Drive <https://drive.google.com/file/d/1Z8PI5bj6_TcQ-n-UBsaSyxwwIE6CKrcg/view?usp=drive_link>`_

What the Module Does
--------------------

A conversion rarely tells the whole acquisition story by itself. A prospect can
arrive from Google Ads, return directly days later, visit through LinkedIn, and
only then submit a Contact Us form. If Direct or the last page overwrites the
known campaign, Sales can see the customer but lose the source that created the
opportunity.

``website_first_last_touch`` keeps two clear acquisition points throughout that
journey:

* **First Touch** — the first valid Website entry that the module is allowed to
  observe. It can be UTM, an advertising click, an external referral, or Direct.
  Once stored, it is not replaced by later visits.
* **Latest Qualified Acquisition** — the latest meaningful acquisition that
  contains supported UTM data, a supported advertising click ID, or a valid
  external referrer. Internal navigation and later Direct returns do not replace
  a known qualified source.

Each touch is stored as one complete snapshot. Source, medium, campaign, term,
content, landing page, referrer, click ID, and timestamp stay together instead
of being mixed between different visits. The result is attribution that remains
understandable when the lead becomes a customer and the opportunity becomes a
sale.

Key Features
------------

* First Touch stays stable even when the visitor returns later through Direct
  traffic or another campaign.
* Latest Qualified Acquisition keeps the most recent meaningful UTM, ad-click,
  or external-referral source without rewarding ordinary navigation.
* Attribution follows the business flow from Website forms to CRM, a newly
  created customer, quotation, and Sales Order.
* UTM source, medium, campaign, term, and content remain together as one
  acquisition snapshot.
* Google Ads ``gclid``, ``gbraid``, and ``wbraid``, Meta / Facebook ``fbclid``,
  and Microsoft Ads ``msclkid`` are supported.
* Landing page and external referrer are preserved with privacy-focused URL
  normalization.
* Standard Website CRM forms work without custom hidden attribution fields.
* CRM and Sales records expose searchable acquisition fields for daily use.
* Native Odoo campaign, source, and medium behavior remains available.
* Existing customers are protected from being overwritten by a new lead's
  acquisition history.
* Lead merges preserve the earliest complete First Touch and latest complete
  qualified acquisition.
* Duplicated leads, customers, and quotations do not inherit stale attribution.
* Consent-aware first-party state is signed and isolated by Website and host.
* Attribution fields are restricted to authorized Sales users.
* No external attribution SaaS, mandatory API key, tracking pixel, or
  third-party Python library is required.

Requirements and Installation
-----------------------------

The module can be installed in Odoo environments that allow custom Python
modules, including Odoo.sh, on-premise installations, and other self-hosted
deployments. Odoo Online does not support third-party Python modules.

The module depends on the standard ``website_crm`` and ``sale_crm``
applications.

#. Copy ``website_first_last_touch`` into an Odoo add-ons path.
#. Restart the Odoo service and update the Apps list.
#. Install **First & Last Touch Attribution - UTM & CRM Tracking**.
#. Confirm that the Website form used for lead generation creates CRM records
   through the standard Odoo Website Form flow.
#. If the Website cookie bar is enabled, keep the standard optional-cookie
   consent flow active. The module follows that decision automatically.

No separate attribution-rule setup is required for normal use. Once installed,
the module works with the standard Website CRM flow and exposes the captured
acquisition on the supported CRM, Customer, and Sales records.

How Attribution Works
---------------------

A normal journey can look like this:

::

   Google Ads visit
       -> First Touch = google / cpc / spring
       -> Latest Qualified Acquisition = google / cpc / spring

   Direct return
       -> First Touch stays Google
       -> Latest Qualified Acquisition stays Google

   LinkedIn campaign
       -> First Touch stays Google
       -> Latest Qualified Acquisition becomes LinkedIn

   Website form submission
       -> CRM Opportunity receives both snapshots
       -> New customer can receive the same attribution
       -> Quotation / Sales Order can keep the acquisition context

This is the central behavior of the module: Direct can be a genuine First Touch,
but a later Direct return does not steal credit from a known qualified campaign.
Marketing keeps the source, and Sales keeps the context on the record it already
uses.

First Touch
-----------

First Touch answers the question: **what was the first Website entry that this
module was allowed to observe for this visitor?**

The first valid touch is written once. A later campaign, referral, reload, or
Direct visit cannot replace it. When optional-cookie consent is required, the
module records only information that is available after Odoo permits optional
cookie storage. It does not reconstruct a visit that occurred before capture was
allowed.

A First Touch can contain:

* UTM source, medium, campaign, term, and content.
* A supported advertising click ID.
* A normalized landing path.
* A sanitized external referrer.
* The acquisition timestamp.
* Direct classification when no qualified acquisition data is present.

Latest Qualified Acquisition
----------------------------

Latest Qualified Acquisition answers a different question: **what was the most
recent meaningful acquisition source before conversion?**

A later touch can replace this snapshot when it contains at least one supported
UTM value, a supported advertising click ID, or a valid external referrer.
Ordinary Direct requests and internal navigation do not replace it.

Repeated identical acquisition data is also handled carefully. The module does
not refresh the stored timestamp only because the same campaign is observed
again. A genuinely different qualified touch can create a new Latest Qualified
Acquisition while the First Touch remains unchanged.

UTM and Advertising Click IDs
-----------------------------

Supported UTM parameters:

::

   utm_source
   utm_medium
   utm_campaign
   utm_term
   utm_content

Supported advertising click IDs:

::

   gclid
   gbraid
   wbraid
   fbclid
   msclkid

These values are stored as part of the complete acquisition snapshot. A later
partial UTM request does not borrow missing source, medium, or campaign values
from an earlier visit. This prevents a false combination that never existed in a
real Website request.

The module also keeps Odoo's native campaign, source, and medium fields working.
It does not replace the standard UTM framework or globally modify every model
that inherits ``utm.mixin``.

Website Forms and CRM
---------------------

The module integrates with the standard Odoo Website Form pipeline. A normal
Website CRM form can create the lead or Opportunity without custom attribution
fields in the form markup.

The attribution available for the current Website request is applied at the
Website Form boundary before the CRM record is created. This also covers a
same-request conversion where a visitor opens a campaign URL and submits the
form without first navigating to another page.

Browser attribution is not read by arbitrary backend creates. A lead created
manually, through an import, RPC/API call, or unrelated backend workflow does
not receive Website attribution merely because a browser cookie exists in the
current session.

Customer and Sales Propagation
------------------------------

Attribution remains useful after the lead has moved deeper into the commercial
workflow.

**New Customer**
  When CRM creates a new customer from an attributed Opportunity, the First
  Touch and Latest Qualified Acquisition are copied to that new customer. The
  customer keeps the acquisition context available at the time of creation.

**Existing Customer**
  Assigning an Opportunity to an existing customer does not overwrite that
  customer's stored attribution. An established customer may have several
  Opportunities and campaigns, so the newest lead is not treated as the event
  that originally acquired the partner.

**Quotation and Sales Order**
  When a quotation is created from an attributed Opportunity through the normal
  CRM sales flow, the complete snapshots are carried into the quotation. The
  attribution then remains visible on the Sales Order created from that
  quotation.

A plain backend Sales Order creation does not read browser state or invent
attribution only because an Opportunity reference is present.

