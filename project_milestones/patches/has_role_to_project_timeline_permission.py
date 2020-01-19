from __future__ import unicode_literals
import frappe
from frappe.utils import cstr


def execute():
	frappe.reload_doc("project_milestones", "doctype", "project_timeline_permission")

	roles = frappe.db.sql("select * from `tabHas Role` where parenttype='Project Timeline'", as_dict=1)
	for d in roles:
		d.doctype = 'Project Timeline Permission'
		d.write = 1 if cstr(d.role).lower() != 'client' else 0

	for d in roles:
		frappe.get_doc(d).insert()

	frappe.db.sql("delete from `tabHas Role` where parenttype='Project Timeline'")
