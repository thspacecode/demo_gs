"""Install hooks for the GS Battery app.

Creates (and on uninstall removes) the *Supplier Quotation Opening Date*
custom field on Request for Quotation that drives the sealed-bid permission.
"""

import frappe

OPENING_DATE_FIELD = "custom_sq_opening_date"
RFQ_DOCTYPE = "Request for Quotation"


def after_install() -> None:
	create_rfq_opening_date_field()


def before_uninstall() -> None:
	remove_rfq_opening_date_field()


def create_rfq_opening_date_field() -> None:
	"""Add `custom_sq_opening_date` (Date) to Request for Quotation."""
	if frappe.db.exists("Custom Field", {"dt": RFQ_DOCTYPE, "fieldname": OPENING_DATE_FIELD}):
		return

	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": RFQ_DOCTYPE,
			"fieldname": OPENING_DATE_FIELD,
			"label": "Supplier Quotation Opening Date",
			"fieldtype": "Date",
			"insert_after": "transaction_date",
			"description": (
				"Supplier Quotations linked to this RFQ cannot be opened before "
				"this date (sealed bid). Leave empty to allow access anytime."
			),
		}
	).insert(ignore_permissions=True)

	frappe.clear_cache(doctype=RFQ_DOCTYPE)


def remove_rfq_opening_date_field() -> None:
	"""Remove the custom field when the app is uninstalled."""
	custom_field = frappe.db.exists(
		"Custom Field", {"dt": RFQ_DOCTYPE, "fieldname": OPENING_DATE_FIELD}
	)
	if custom_field:
		frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True)
		frappe.clear_cache(doctype=RFQ_DOCTYPE)
