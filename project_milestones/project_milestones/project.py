import frappe
from frappe import _
from six import string_types, iteritems
import json


def validate(self, method):
	check_duplicates_stages(self)
	reorder_stages(self)
	validate_document_status(self)
	set_document_status(self)
	validate_stage_status(self)
	update_costing(self)


def onload(self, method):
	update_costing(self)


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


def validate_document_status(self):
	for d in self.documents:
		if d.document_status == "Approved":
			if not d.submitted_attachment:
				frappe.throw(_("Cannot Approve {0} document {1} if document is not uploaded")
					.format(d.project_timeline, frappe.bold(d.document_name)))
			if not d.reviewed_attachment:
				frappe.throw(_("Cannot Approve {0} document {1} if reviewed document is not uploaded")
					.format(d.project_timeline, frappe.bold(d.document_name)))


def set_document_status(self):
	for d in self.documents:
		if d.submitted_attachment:
			if d.reviewed_attachment:
				if d.document_status != "Approved":
					d.document_status = "Pending Approval"
			else:
				d.document_status = "Pending Approval"
		else:
			d.document_status = "Awaiting Upload"


def validate_stage_status(self):
	document_map = get_timeline_stage_document_map(self)

	for d in self.stages:
		if d.stage_status == "Completed":
			any_unapproved = any([d.document_status != "Approved" for d in document_map[d.project_timeline][d.project_stage]])
			if any_unapproved:
				frappe.throw(_("Cannot set status of {0} stage {1} as Completed because some documents still require approval")
					.format(d.project_timeline, frappe.bold(d.project_stage)))


def get_timeline_stage_document_map(self):
	document_map = {}
	for d in self.stages:
		document_map.setdefault(d.project_timeline, {}).setdefault(d.project_stage, [])
	for d in self.documents:
		document_map.setdefault(d.project_timeline, {}).setdefault(d.project_stage, []).append(d)

	return document_map


def get_timeline_stage_map(self):
	stage_map = {}
	for d in self.stages:
		stage_map.setdefault(d.project_timeline, []).append(d.as_dict())

	for stages in stage_map.values():
		for i, stage in enumerate(stages):
			stage.idx = i + 1

	for timeline, stages in iteritems(stage_map):
		last_in_progress = None
		last_completed = None
		for stage in stages:
			if stage.stage_status == "In Progress":
				last_in_progress = stage
			elif stage.stage_status == "Completed":
				last_completed = stage

		if last_in_progress:
			last_in_progress.selected = 1
		elif last_completed:
			last_completed.selected = 1
		elif stages:
			stages[0].selected = 1

	return stage_map


def on_po_submit_cancel(self, method):
	projects = []
	for d in self.items:
		if d.project:
			projects.append(d.project)

	for project_name in set(projects):
		update_project_po_value(project_name)


def on_pe_submit_cancel(self, method):
	if self.project:
		update_project_paid_amount(self.project)


def on_jv_submit_cancel(self, method):
	projects = []
	for d in self.accounts:
		if d.project:
			projects.append(d.project)

	for project_name in set(projects):
		update_project_paid_amount(project_name)


def update_costing(self):
	self.total_po_value = update_project_po_value(self.name, db_update=False)
	self.total_paid_amount = update_project_paid_amount(self.name, db_update=False)
	self.total_pending_amount = self.total_po_value - self.total_paid_amount


def update_project_po_value(project_name, db_update=True):
	total_purchase_cost = frappe.db.sql("""select sum(base_net_amount)
		from `tabPurchase Order Item` where project = %s and docstatus=1""", project_name)
	total_purchase_cost = total_purchase_cost and total_purchase_cost[0][0] or 0

	if db_update:
		frappe.db.set_value("Project", project_name, "total_po_value", total_purchase_cost)

	return total_purchase_cost


def update_project_paid_amount(project_name, db_update=True):
	pe_amount = frappe.db.sql("""select sum(base_paid_amount)
		from `tabPayment Entry` where project = %s and docstatus=1""", project_name)
	jv_amount = frappe.db.sql("""select sum(debit-credit)
		from `tabJournal Entry Account` where project = %s and docstatus=1""", project_name)

	total_paid_amount = pe_amount and pe_amount[0][0] or 0
	total_paid_amount += jv_amount and jv_amount[0][0] or 0

	if db_update:
		frappe.db.set_value("Project", project_name, "total_paid_amount", total_paid_amount)

	return total_paid_amount


@frappe.whitelist()
def get_stages_from_project_type(project_type):
	if not project_type:
		frappe.throw(_("Project Type not provided"))

	doc = frappe.get_cached_doc("Project Type", project_type)
	stages = [{"project_timeline": d.project_timeline, "project_stage": d.project_stage} for d in doc.stages]
	stages = sorted(stages, key=lambda d: d.get('project_timeline'))
	return stages


@frappe.whitelist()
def get_documents_from_project_stages(project_stages):
	if project_stages and isinstance(project_stages, string_types):
		project_stages = json.loads(project_stages)

	if not project_stages:
		frappe.throw(_("Project Stage not provided"))

	documents = []
	for d in project_stages:
		for document_name in get_project_stage_documents(d['project_stage']):
			documents.append({
				"project_timeline": d.get("project_timeline"),
				"project_stage": d.get("project_stage"),
				"document_name": document_name
			})

	return documents


def get_project_stage_documents(project_stage):
	doc = frappe.get_cached_doc("Project Stage", project_stage)
	return [d.document_name for d in doc.documents]


@frappe.whitelist()
def get_timeline_stage_documents(project_name, timeline, stage):
	project = frappe.get_doc("Project", project_name)

	documents = project.get("documents", {"project_timeline": timeline, "project_stage": stage})
	for i, d in enumerate(documents):
		d.idx = i + 1

	return documents
