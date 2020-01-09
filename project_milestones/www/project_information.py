from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from project_milestones.project_milestones.project import get_timeline_stage_map,\
	get_supplier_wise_project_order_billing_payment, check_project_user_permission, has_clear_attachment_permission,\
	has_comment_section_permission


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
	context.stage_map, context.single_stage_timelines = get_timeline_stage_map(context.doc)
	context.supplier_map = get_supplier_wise_project_order_billing_payment(context.doc.name)
	context.comment_map = get_comment_map(context.doc.name)
	context.can_clear_attachments = cint(has_clear_attachment_permission())

	# Title and breadcrumbs
	context.title = _("Project Information")
	context.parents = [
		{'title': _('Projects'), 'route': '/project'},
	]


def get_comment_map(name):
	comment_sections = frappe.get_all("Project Comment Section")

	comments = frappe.get_all('Comment',
		fields=['name', 'creation', 'owner', 'comment_email', 'comment_by', 'content', 'project_comment_section'],
		filters=dict(
			reference_doctype="Project",
			reference_name=name,
			comment_type='Comment',
			published=1
		),
		order_by='creation asc'
	)

	comment_map = {}

	for d in comment_sections:
		if has_comment_section_permission(d.name):
			comment_map[d.name] = []

	for d in comments:
		if d.project_comment_section and d.project_comment_section in comment_map:
			comment_map[d.project_comment_section].append(d)

	return comment_map
