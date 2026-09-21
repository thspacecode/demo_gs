# GS Battery

Customizations for the GS Battery procurement demo.

## Feature: Sealed Supplier Quotations

A new Date field **Supplier Quotation Opening Date** (`custom_sq_opening_date`)
is added to **Request for Quotation**.

Until that date is reached, Supplier Quotations linked to the RFQ are *sealed*:

- **Nobody** can **open/read** them (list view, form view, print, API) —
  not even `Administrator`. The only exception is a **website/portal user who
  owns the document** (the supplier who submitted the bid via the portal).
- They are hidden from list/report/link views for everyone else.
- Creating, editing and submitting quotations is **not** blocked, so suppliers
  can still submit their bids before the opening date.

Once the opening date is reached (or no date is set on the RFQ), access works
as normal.

Implemented via:

- `has_permission` hook on *Supplier Quotation* (blocks all non-Administrator users)
- `override_doctype_class` → `SealedSupplierQuotation.has_permission()` — blocks
  `Administrator` too, because Frappe bypasses `has_permission` hooks for Administrator
- `permission_query_conditions` hook on *Supplier Quotation* (hides sealed docs
  from lists/reports/link search for everyone, Administrator included)
- Custom Field created by `after_install` (removed again by `before_uninstall`)
