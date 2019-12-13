import frappe
from frappe import _


def validate(self, method):
	check_duplicates_stages(self)
	reorder_stages(self)


def check_duplicates_stages(self):
	unique = set()
	for d in self.stages:
		key = (d.project_timeline, d.project_stage)
		if key in unique:
			frappe.throw(_("Row #{0}: {1}, {2} is a duplicate".format(d.idx, d.project_timeline, d.project_stage)))
		else:
			unique.add(key)


def reorder_stages(self):
	self.stages = sorted(self.stages, key=lambda d: d.project_timeline)
	for i, d in enumerate(self.stages):
		d.idx = i + 1
