app_name = "gs_battery"
app_title = "GS Battery"
app_publisher = "GS Battery"
app_description = "Customizations for the GS Battery procurement demo"
app_email = "demo@gsbattery.example.com"
app_license = "mit"

# Installation
# ------------
after_install = "gs_battery.install.after_install"
before_uninstall = "gs_battery.install.before_uninstall"

# Permissions
# -----------
# Sealed-bid rule: Supplier Quotations linked to a Request for Quotation whose
# "Supplier Quotation Opening Date" (custom_sq_opening_date) is in the future
# cannot be opened by anyone except the document owner — Administrator
# included (enforced via the controller override below).

has_permission = {
	"Supplier Quotation": "gs_battery.permissions.supplier_quotation_has_permission",
}

permission_query_conditions = {
	"Supplier Quotation": "gs_battery.permissions.supplier_quotation_permission_query_conditions",
}

# Document overrides
# ------------------
# Blocks read permission checks for Administrator too (Frappe bypasses
# has_permission hooks for Administrator, so a hook alone is not enough).
override_doctype_class = {
	"Supplier Quotation": "gs_battery.overrides.SealedSupplierQuotation",
}
