import frappe
from frappe import _
from project_milestones.project_milestones.project import check_duplicates_stages, validate_single_stage_timeline, reorder_stages


def validate(self, method):
	check_duplicates_stages(self)
	validate_single_stage_timeline(self, 'stages')
	reorder_stages(self)
