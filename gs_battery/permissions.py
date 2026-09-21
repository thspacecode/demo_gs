"""Permission logic for the GS Battery "sealed bid" demo.

Rule
----
A Supplier Quotation that is linked (via its items) to a Request for Quotation
that defines a *Supplier Quotation Opening Date* (`custom_sq_opening_date`)
in the future is **sealed**: no user may open (read) it yet — not even
``Administrator``.

The only exception is a **website/portal user who owns the document** – i.e.
the supplier who submitted the bid through the supplier portal – who may
always open their own quotation. Internal users (``System User``), including
``Administrator``, get **no** exemption.

Only ``read`` is restricted. ``create``/``write``/``submit``/... are left
untouched so that suppliers can still prepare and submit their bids before
the opening date.

Enforcement points
------------------
1. ``has_permission`` hook (below) – blocks every non-Administrator user.
   (Frappe never calls this hook for Administrator.)
2. ``override_doctype_class`` (``gs_battery.overrides.SealedSupplierQuotation``)
   – overrides ``Document.has_permission`` so that ``doc.check_permission()``
   also blocks ``Administrator`` on form load / REST API / print.
3. ``permission_query_conditions`` hook (below) – hides sealed quotations
   from list / report / link views for every user, including Administrator.
"""

import frappe
from frappe import _
from frappe.utils import format_date, today

OPENING_DATE_FIELD = "custom_sq_opening_date"
SQ_DOCTYPE = "Supplier Quotation"
RFQ_DOCTYPE = "Request for Quotation"
SQ_ITEM_DOCTYPE = "Supplier Quotation Item"


def _get_linked_rfq_names(doc) -> list[str]:
	"""Return the distinct RFQ names linked from the Supplier Quotation items."""
	return list(
		{
			item.request_for_quotation
			for item in (doc.get("items") or [])
			if item.request_for_quotation
		}
	)


def _get_sealing_rfqs(rfq_names: list[str]) -> list[frappe._dict]:
	"""Return linked RFQs whose opening date is set and still in the future."""
	if not rfq_names:
		return []
	return frappe.get_all(
		RFQ_DOCTYPE,
		filters={"name": ("in", rfq_names), OPENING_DATE_FIELD: (">", today())},
		fields=["name", OPENING_DATE_FIELD],
		order_by=OPENING_DATE_FIELD,
	)


def is_exempt_owner(doc, user) -> bool:
	"""Whether ``user`` may open the sealed ``doc`` because they own it.

	Only *website/portal users* (e.g. the supplier who submitted the bid)
	get this exemption. Internal users (``System User``) — Administrator
	included — are never exempt.
	"""
	if not user or (doc.get("owner") or "").lower() != user.lower():
		return False
	return frappe.get_cached_value("User", user, "user_type") == "Website User"


def assert_not_sealed(doc) -> None:
	"""Throw a PermissionError (with a Thai explanation) if the SQ is sealed."""
	sealing_rfqs = _get_sealing_rfqs(_get_linked_rfq_names(doc))
	if not sealing_rfqs:
		return

	rfq = sealing_rfqs[0]
	frappe.throw(
		_(
			"ไม่สามารถเปิด Supplier Quotation นี้ได้ในขณะนี้ (Sealed Bid)<br>"
			"เอกสารนี้เชื่อมกับ Request for Quotation {0} ซึ่งกำหนดวันเปิดซองเสนอราคาไว้ที่ {1}<br>"
			"กรุณารอจนถึงวันที่กำหนด จึงจะสามารถเปิดดูเอกสารได้"
		).format(
			frappe.bold(rfq.name),
			frappe.bold(format_date(rfq[OPENING_DATE_FIELD])),
		),
		frappe.PermissionError,
		title=_("Supplier Quotation ยังไม่ถึงวันเปิดซอง"),
	)


def supplier_quotation_has_permission(doc, ptype, user=None, debug=False) -> bool:
	"""``has_permission`` hook for Supplier Quotation.

	Hooks can only *deny* permissions in Frappe; return ``True`` to abstain
	(i.e. let the standard role permissions decide) and throw / return
	``False`` to deny.

	Note: Frappe short-circuits this hook for ``Administrator`` — the
	Administrator block lives in the controller override instead.
	"""
	# Only opening the document is restricted; creating/updating/submitting
	# quotations before the opening date must keep working.
	if ptype != "read" or doc is None:
		return True

	user = user or frappe.session.user
	if is_exempt_owner(doc, user):
		return True

	assert_not_sealed(doc)
	return True


def supplier_quotation_permission_query_conditions(user, doctype=None) -> str:
	"""``permission_query_conditions`` hook for Supplier Quotation.

	Hides sealed Supplier Quotations from list / report / link search views.
	Applies to **every** user (including Administrator); only a website/portal
	user still sees their own sealed quotation.
	"""
	user = user or frappe.session.user

	conditions = f"""
		not exists (
			select 1
			from `tab{SQ_ITEM_DOCTYPE}` sq_item
			inner join `tab{RFQ_DOCTYPE}` rfq
				on rfq.`name` = sq_item.`request_for_quotation`
			where sq_item.`parent` = `tab{SQ_DOCTYPE}`.`name`
				and rfq.`{OPENING_DATE_FIELD}` > curdate()
		)
	"""

	if frappe.get_cached_value("User", user, "user_type") == "Website User":
		# Portal users (suppliers) still see their own bids.
		conditions = f"""
			`tab{SQ_DOCTYPE}`.`owner` = {frappe.db.escape(user, percent=False)}
			or {conditions}
		"""

	return f"({conditions})"
