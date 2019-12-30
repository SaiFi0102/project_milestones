from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from project_milestones.project_milestones.project import get_timeline_stage_map,\
	get_supplier_wise_project_order_billing_payment, check_project_user_permission
from frappe.website.utils import get_comment_list


def get_context(context):
	def has_field_permission(fieldname, parent=None, ptype='read'):
		meta = context.doc.meta
		if parent:
			table_field = meta.get_field(parent)
			table_dt = table_field.options

			meta = frappe.get_meta(table_dt)

		df = meta.get_field(fieldname)
		return cint((df.permlevel or 0) == 0 or context.doc.has_permlevel_access_to(fieldname, df, ptype))

	context.has_field_permission = has_field_permission
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
	]
