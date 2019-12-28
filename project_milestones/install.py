from __future__ import unicode_literals
import frappe
from frappe.core.doctype.file.file import create_new_folder

def after_install():
	if not frappe.get_all("File", filters={"folder": "Home", "file_name": "Project Documents", "is_folder": 1}, limit=1):
		create_new_folder("Project Documents", "Home")

	frappe.db.commit()