import frappe
from frappe import _
from frappe.utils import flt, cint
from six import string_types, iteritems
from frappe.model.meta import get_field_precision
from frappe.utils import get_fullname
import json
import os


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


def set_document_status(self):
	for d in self.documents:
		if d.submitted_attachment:
			if d.document_status != "Approved":
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


def get_timeline_stage_map(self, ignore_permissions=False):
	stage_map = {}
	for d in self.stages:
		stage_map.setdefault(d.project_timeline, []).append(d.as_dict())

	if not ignore_permissions:
		to_remove = []
		for project_timeline in stage_map.keys():
			if not has_project_timeline_permission(project_timeline):
				to_remove.append(project_timeline)

		for project_timeline in to_remove:
			del stage_map[project_timeline]

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
	data = get_total_project_order_billing_payment(self.name)
	self.update(data)


def update_project_po_value(project_name):
	data = get_total_project_order_billing_payment(project_name)
	frappe.db.set_value("Project", project_name, "total_po_amount", data.total_po_amount)


def update_project_paid_amount(project_name):
	data = get_total_project_order_billing_payment(project_name)
	frappe.db.set_value("Project", project_name, "total_paid_amount", data.total_paid_amount)


def get_total_project_order_billing_payment(project_name):
	po_data, pinv_data = get_project_po_pinv_data(project_name)

	out = frappe._dict({
		"total_purchase_cost": 0, "total_po_amount": 0, "total_paid_amount": 0, "total_outstanding_amount": 0
	})

	for d in po_data:
		out.total_po_amount += d.base_net_total
		out.total_paid_amount += d.paid_amount

	for d in pinv_data:
		out.total_purchase_cost += d.base_net_total
		out.total_outstanding_amount += d.outstanding_amount
		out.total_paid_amount += d.paid_amount

	for field, value in iteritems(out):
		precision = get_field_precision(frappe.get_meta("Project").get_field(field))
		out[field] = flt(out[field], precision)

	return out


def get_supplier_wise_project_order_billing_payment(project_name):
	po_data, pinv_data = get_project_po_pinv_data(project_name)

	supplier_map = {}
	for d in po_data + pinv_data:
		supplier_map.setdefault(d.supplier, frappe._dict({
			"supplier": d.supplier, "purchase_cost": 0, "po_amount": 0, "paid_amount": 0, "outstanding_amount": 0
		}))

	for d in po_data:
		supplier_map[d.supplier].po_amount += d.base_net_total
		supplier_map[d.supplier].paid_amount += d.paid_amount

	for d in pinv_data:
		supplier_map[d.supplier].billed_amount += d.base_net_total
		supplier_map[d.supplier].outstanding_amount += d.outstanding_amount
		supplier_map[d.supplier].paid_amount += d.paid_amount

	for supplier_data in supplier_map.values():
		for field, value in iteritems(supplier_data):
			if field != "supplier":
				precision = get_field_precision(frappe.get_meta("Project").get_field("total_" + field))
				supplier_data[field] = flt(supplier_data[field], precision)

	return supplier_map


def get_project_po_pinv_data(project_name):
	po_data = frappe.db.sql("""
		select p.name, p.supplier, p.base_net_total, 0 as paid_amount
		from `tabPurchase Order` p
		where p.docstatus = 1
			and exists(select name from `tabPurchase Order Item` i where i.parent = p.name and i.project = %s)
	""", project_name, as_dict=1)

	po_map = {}
	for d in po_data:
		po_map[d.name] = d

	pinv_data = frappe.db.sql("""
		select p.name, p.supplier, p.base_net_total, 0 as paid_amount, p.outstanding_amount
		from `tabPurchase Invoice` p
		where p.docstatus = 1
			and exists(select name from `tabPurchase Invoice Item` i where i.parent = p.name and i.project = %s)
	""", project_name, as_dict=1)

	pinv_map = {}
	for d in pinv_data:
		pinv_map[d.name] = d

	unique_pos = [d.name for d in po_data]
	unique_pinvs = [d.name for d in pinv_data]

	gle_against_po = frappe.db.sql("""
		select against_voucher, sum(debit-credit) as amount
		from `tabGL Entry`
		where against_voucher_type = 'Purchase Order' and against_voucher in %s
		group by against_voucher
	""", [unique_pos], as_dict=1) if unique_pos else []

	for d in gle_against_po:
		po_map[d.against_voucher].paid_amount += d.amount

	gle_against_pinv = frappe.db.sql("""
		select against_voucher, sum(debit-credit) as amount
		from `tabGL Entry`
		where against_voucher_type = 'Purchase Invoice' and against_voucher in %s
			and (voucher_type, voucher_no) != (against_voucher_type, against_voucher)
		group by against_voucher
	""", [unique_pinvs], as_dict=1) if unique_pinvs else []

	for d in gle_against_pinv:
		pinv_map[d.against_voucher].paid_amount += d.amount

	return po_data, pinv_data


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


@frappe.whitelist()
def download_document(docname, fieldname):
	validate_document_fieldname(fieldname)

	project_name, project_timeline, file_url = frappe.db.get_value("Project Document", docname,
		['parent', 'project_timeline', fieldname])

	check_project_user_permission(project_name)
	check_project_timeline_permission(project_timeline)

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	frappe.local.response.filename = os.path.basename(file_url)
	frappe.local.response.filecontent = file_doc.get_content()

	if file_url.endswith('.pdf'):
		frappe.local.response.type = "pdf"
	else:
		frappe.local.response.type = "download"


@frappe.whitelist()
def upload_document():
	docname = frappe.form_dict.docname
	fieldname = frappe.form_dict.folder

	validate_document_fieldname(fieldname)

	project_name, project_timeline = frappe.db.get_value("Project Document", docname, ['parent', 'project_timeline'])

	check_project_user_permission(project_name)
	check_project_timeline_permission(project_timeline)

	file_doc = frappe.get_doc({
		"doctype": "File",
		"attached_to_doctype": "Project",
		"attached_to_name": project_name,
		"folder": 'Home/Project Documents',
		"file_name": frappe.local.uploaded_filename,
		"file_url": frappe.form_dict.file_url,
		"is_private": 1,
		"content": frappe.local.uploaded_file
	})
	file_doc.save()

	file_url = file_doc.file_url

	project = frappe.get_doc("Project", project_name)
	document_row = project.get("documents", filters={"name": docname})
	if not document_row:
		frappe.throw(_("Invalid Document Selected"))

	document_row = document_row[0]
	if document_row.get(fieldname):
		frappe.throw(_("Document is already uploaded"))

	document_row.set(fieldname, file_url)
	document_row.set(fieldname + "_date", frappe.utils.today())
	project.save()

	frappe.msgprint(_("{0} Document {1} {2} has been successfully uploaded").format(document_row.project_timeline,
		frappe.bold(document_row.document_name), frappe.unscrub(fieldname)))

	return file_doc


@frappe.whitelist()
def set_document_client_view(docname, value):
	project_name, project_timeline = frappe.db.get_value("Project Document", docname, ['parent', 'project_timeline'])

	check_project_user_permission(project_name)
	check_project_timeline_permission(project_timeline)

	project = frappe.get_doc("Project", project_name)
	document_row = project.get("documents", filters={"name": docname})
	if not document_row:
		frappe.throw(_("Invalid Document Selected"))

	document_row = document_row[0]
	document_row.client_view = cint(value)
	project.save()

	allowed_disallowed = "allowed" if document_row.client_view else "disallowed"
	frappe.msgprint(_("{0} Document {1} is now {2} for client view").format(document_row.project_timeline,
		frappe.bold(document_row.document_name), allowed_disallowed))


@frappe.whitelist()
def approve_document(docname):
	project_name, project_timeline = frappe.db.get_value("Project Document", docname, ['parent', 'project_timeline'])

	check_project_user_permission(project_name)
	check_project_timeline_permission(project_timeline)

	project = frappe.get_doc("Project", project_name)
	document_row = project.get("documents", filters={"name": docname})
	if not document_row:
		frappe.throw(_("Invalid Document Selected"))

	document_row = document_row[0]
	if document_row.document_status == "Approved":
		frappe.throw(_("Document is already approved"))

	document_row.document_status = "Approved"
	project.save()

	frappe.msgprint(_("{0} Document {1} has been successfully <b>Approved</b>").format(document_row.project_timeline,
		frappe.bold(document_row.document_name)))


@frappe.whitelist()
def add_comment(project_name, comment):
	check_project_user_permission(project_name)

	comment_doc = frappe.get_doc({
		"doctype": "Comment",
		'comment_type': "Comment",
		"comment_email": frappe.session.user,
		"comment_by": get_fullname(frappe.session.user),
		"reference_doctype": "Project",
		"reference_name": project_name,
		"content": comment,
		"published": 1
	}).insert(ignore_permissions=True)

	template = frappe.get_template("templates/includes/comments/comment.html")
	return template.render({"comment": comment_doc.as_dict()})


def validate_document_fieldname(fieldname):
	if fieldname not in ['submitted_attachment', 'reviewed_attachment']:
		frappe.throw(_("Incorrect Field Name"))


def check_project_user_permission(project_name, user=None):
	if not user:
		user = frappe.session.user

	project_user = frappe.db.get_value("Project User",
		{"parent": project_name, "user": user}, ["user", "view_attachments"], as_dict=True)
	if frappe.session.user != 'Administrator' and (not project_user or frappe.session.user == 'Guest'):
		raise frappe.PermissionError


def check_project_timeline_permission(project_timeline, user=None):
	if not has_project_timeline_permission(project_timeline, user):
		raise frappe.PermissionError


def has_project_timeline_permission(project_timeline, user=None):
	doc = frappe.get_cached_doc("Project Timeline", project_timeline)
	allowed_roles = [d.role for d in doc.allowed_roles]
	user_roles = frappe.get_roles(user)

	for role in user_roles:
		if role in allowed_roles:
			return True

	return False


'''
pe_unallocated_amount = frappe.db.sql("""
		select party, sum(unallocated_amount)
		from `tabPayment Entry`
		where docstatus=1 and party_type='Supplier' and project = %s
		group by party
	""", project_name)
	pe_against_po_amount = frappe.db.sql("""
		select pe.party, sum(pref.allocated_amount)
		from `tabPayment Entry Reference` pref
		inner join `tabPayment Entry` pe on pe.name = pref.parent
		where pe.docstatus=1 and pe.party_type='Supplier'
			and pref.reference_doctype = 'Purchase Order' and pref.reference_name in %s
		group by party
	""", [unique_pos])
	pe_against_pinv_amount = frappe.db.sql("""
		select pe.party, sum(pref.allocated_amount)
		from `tabPayment Entry Reference` pref
		inner join `tabPayment Entry` pe on pe.name = pref.parent
		where pe.docstatus=1 and pe.party_type='Supplier'
			and pref.reference_doctype = 'Purchase Invoice' and pref.reference_name in %s
		group by party
	""", [unique_pinvs])

	jv_unallocated_amount = frappe.db.sql("""
		select party, sum(debit-credit)
		from `tabJournal Entry Account`
		where docstatus=1 and party_type='Supplier' and ifnull(reference_name, '') = '' and project = %s
	""", project_name)
	jv_against_po_amount = frappe.db.sql("""
		select party, sum(debit-credit)
		from `tabJournal Entry Account`
		where docstatus=1 and party_type='Supplier' and reference_type = 'Purchase Order' and reference_name in %s
	""", [unique_pos])
	jv_against_pinv_amount = frappe.db.sql("""
		select party, sum(debit-credit)
		from `tabJournal Entry Account`
		where docstatus=1 and party_type='Supplier' and reference_type = 'Purchase Invoice' and reference_name in %s
	""", [unique_pinvs])
'''