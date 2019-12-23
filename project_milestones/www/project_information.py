from __future__ import unicode_literals
import frappe
from frappe import _
from project_milestones.project_milestones.project import get_timeline_stage_map,\
	get_supplier_wise_project_order_billing_payment


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True

	# Redirect if project name not given
	if not frappe.form_dict.project:
		frappe.local.flags.redirect_location = "/project"
		raise frappe.Redirect

	# Check project user permission
	project_user = frappe.db.get_value("Project User",
		{"parent": frappe.form_dict.project, "user": frappe.session.user}, ["user", "view_attachments"], as_dict=True)
	if frappe.session.user != 'Administrator' and (not project_user or frappe.session.user == 'Guest'):
		raise frappe.PermissionError

	# Get project doc context
	context.doc = frappe.get_doc("Project", frappe.form_dict.project)
	context.doc.run_method("onload")
	context.stage_map = get_timeline_stage_map(context.doc)
	context.supplier_map = get_supplier_wise_project_order_billing_payment(context.doc.name)

	# Title and breadcrumbs
	context.title = _("Project Information")
	context.parents = [
		{'title': _('Projects'), 'route': '/project'},
		{'title': context.doc.project_name, 'route': '/projects?project=' + context.doc.name}
	]
