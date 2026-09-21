"""Controller overrides for the GS Battery "sealed bid" demo.

Frappe short-circuits permission checks for ``Administrator`` *before* the
``has_permission`` hooks run, so a hook alone can never block Administrator.

Overriding the Supplier Quotation controller's ``has_permission`` method
closes that gap: every ``doc.check_permission("read")`` call — desk form
load, REST API (``frappe.client.get``), print view, etc. — now runs the
sealed-bid check for **all** users, including Administrator.

Plain ``frappe.get_doc(...)`` (business logic, background jobs, imports)
does not perform permission checks and is therefore unaffected.
"""

import frappe
from erpnext.buying.doctype.supplier_quotation.supplier_quotation import (
	SupplierQuotation,
)

from gs_battery.permissions import assert_not_sealed, is_exempt_owner


class SealedSupplierQuotation(SupplierQuotation):
	"""Supplier Quotation controller that enforces the sealed-bid rule for everyone."""

	def has_permission(self, permtype="read", *, debug=False, user=None) -> bool:
		if permtype == "read" and not self.flags.ignore_permissions:
			check_user = user or frappe.session.user
			if not is_exempt_owner(self, check_user):
				# Raises frappe.PermissionError with a Thai explanation when sealed.
				# Applies to ALL internal users — Administrator included.
				assert_not_sealed(self)
		return super().has_permission(permtype, debug=debug, user=user)
