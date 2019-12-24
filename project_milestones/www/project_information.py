from __future__ import unicode_literals
import frappe
from frappe import _
from project_milestones.project_milestones.project import get_timeline_stage_map,\
	get_supplier_wise_project_order_billing_payment, check_project_user_permission
from frappe.website.utils import get_comment_list


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True

	# Redirect if project name not given
	if not frappe.form_dict.project:
		frappe.local.flags.redirect_location = "/project"
		raise frappe.Redirect

	# Check project user permission
	check_project_user_permission(frappe.form_dict.project)

	# Get project doc context
	context.doc = frappe.get_doc("Project", frappe.form_dict.project)
	context.doc.run_method("onload")
	context.stage_map = get_timeline_stage_map(context.doc)
	context.supplier_map = get_supplier_wise_project_order_billing_payment(context.doc.name)
	context.comment_list = get_comment_list(context.doc.doctype, context.doc.name)

	# Title and breadcrumbs
	context.title = _("Project Information")
	context.parents = [
		{'title': _('Projects'), 'route': '/project'},
		{'title': context.doc.project_name, 'route': '/projects?project=' + context.doc.name}
	]
