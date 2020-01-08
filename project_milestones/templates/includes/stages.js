frappe.provide("project_milestones.stages");

project_milestones.stages.set_stage = function(timeline, stage) {
	if (!timeline || !stage) {
		return;
	}
	if(!$(`.timeline-document-section[data-timeline='${timeline}']`).length) {
		return;
	}

	const $all_buttons = $(`.btn-stage[data-timeline='${timeline}']`);
	$all_buttons.data('selected', 0);
	$all_buttons.removeClass('btn-primary').addClass('btn-default');

	const $selected = $(`.btn-stage[data-timeline='${timeline}'][data-stage='${stage}']`);
	$selected.data('selected', 1);
	$selected.removeClass('btn-default').addClass('btn-primary');

	project_milestones.stages.load_documents(timeline, stage);
};

project_milestones.stages.load_documents = function(timeline, stage) {
	if (!timeline || !stage) {
		return;
	}
	if(!$(`.timeline-document-section[data-timeline='${timeline}']`).length) {
		return;
	}

	return frappe.call({
		method: "project_milestones.project_milestones.project.get_timeline_stage_documents",
		args: {
			project_name: cur_project,
			timeline: timeline,
			stage: stage
		},
		freeze: 1,
		callback: function(r) {
			if (r.message) {
				const $tbody = $(`tbody[data-timeline='${timeline}']`);
				$tbody.empty();

				let field_list = project_milestones.stages.make_table_field_list(timeline);

				if (r.message && r.message.length) {
					$(`.timeline-document-section[data-timeline='${timeline}']`).show();
					$.each(r.message || [], function (i, document) {
						let $tr = $('<tr></tr>');
						$.each(field_list || [], function (i, field) {
							let $td = $('<td></td>');
							$td.data('fieldname', field.fieldname);
							$td.append(project_milestones.make_table_field(field, document));

							if (field.style) {
								$td.attr('style', field.style);
							}
							if (field.class) {
								$td.attr('class', field.class);
							}

							$tr.append($td);
						});

						$tbody.append($tr);
					});
				} else if(field_list.length) {
					$(`.timeline-document-section[data-timeline='${timeline}']`).hide();
					//let $tr = $(`<tr><td class="text-center" colspan="${field_list.length}">${__('No documents to show')}</td></tr>`);
					//$tbody.append($tr);
				}
			}
		}
	});
};

// Make fields list from thead
project_milestones.stages.make_table_field_list = function(timeline) {
	let field_list = [];

	const $ths = $(`th[data-timeline='${timeline}']`);
	$ths.each(function (i, th) {
		const fieldname = $(th).data('fieldname');
		const fieldtype = $(th).data('fieldtype');
		const canwrite = $(th).data('canwrite');
		const style = $(th).attr('style');
		const classStr = $(th).attr('class');

		if (fieldname) {
			field_list.push({fieldname: fieldname, fieldtype: fieldtype, style: style, class: classStr, canwrite: canwrite});
		}
	});

	return field_list;
};

// Make table field name
project_milestones.make_table_field = function(field, doc) {
	let $value;
	const value = doc[field.fieldname];

	if (field.fieldtype === "Check") {
		$value = $(`<input type="checkbox" />`);
		if (cint(value)) {
			$value.attr('checked', 1);
		}

		if (cint(field.canwrite)) {
			$value.change(function () {
				project_milestones.stages.set_document_client_view(doc.name, this.checked,
					doc.project_timeline, doc.project_stage)
			});
		} else {
			$value.attr("disabled", 1);
		}
	} else if(field.fieldtype === "Attach") {
		$value = $(`<button type="button" class="btn btn-sm"></button>`);

		if (value) {
			$value.text(__("View"));
			$value.addClass('btn-info');
			$value.click(() => project_milestones.stages.view_document(doc.name, field.fieldname));
		} else if (cint(field.canwrite)) {
			$value.text(__("Attach"));
			$value.addClass('btn-primary');
			$value.click(() => project_milestones.stages.attach_document(doc.name, field.fieldname,
				doc.project_timeline, doc.project_stage));
		} else {
			$value.text(__("Not Attached"));
			$value.addClass('btn-default');
			$value.attr("disabled", 1);
		}
	} else if (field.fieldtype === "Status") {
		if (["Pending Approval", "Review Required"].includes(value) && cint(field.canwrite)) {
			const button_id = `dropdown-t${cstr(doc.project_timeline)}-s${cstr(doc.project_stage)}`;

			$value = $(`<div class="dropdown"></div>`);
			const $button = $(`<button type="button" class="btn btn-sm btn-warning dropdown-toggle" id="${button_id}" aria-haspopup="true" aria-expanded="true">${__(value)}</button>`);
			const $dropdown_div = $(`<div class="dropdown-menu" aria-labelledby="${button_id}"></div>`);

			const $approve = $(`<a class="dropdown-item" href="#">${__("Approve")}</a>`);
			$approve.click(() => {
				project_milestones.stages.approve_document(doc.name, doc.document_name,
					doc.project_timeline, doc.project_stage);
				return false;
			});
			$dropdown_div.append($approve);

			if (value !== "Review Required") {
				const $request_review = $(`<a class="dropdown-item" href="#">${__("Request Review")}</a>`);
				$request_review.click(() => {
					project_milestones.stages.request_review_document(doc.name, doc.document_name,
						doc.project_timeline, doc.project_stage);
					return false;
				});
				$dropdown_div.append($request_review);
			}

			$button.click(() => $dropdown_div.toggle());

			$value.append($button);
			$value.append($dropdown_div);
			return $value;
		} else {
			$value = $(`<small></small>`);
			$value.text(__(value));
			if (value === "Approved") {
				$value.css('color', 'darkgreen');
				$value.css('font-weight', 'bold');
			} else if (value === "Awaiting Upload") {
				$value.css('color', 'brown');
			}
		}
	} else if (field.fieldtype === "Date") {
		const formatted_date = frappe.format(value, {fieldtype: "Date"});
		$value = $(`<small></small>`);
		$value.text(formatted_date);
	} else {
		$value = $(`<small></small>`);
		$value.text(__(value));
	}

	return $value;
};

project_milestones.stages.attach_document = function(docname, fieldname, timeline, stage) {
	return new frappe.ui.FileUploader({
		doctype: "Project Document",
		docname: docname,
		folder: fieldname,
		method: "project_milestones.project_milestones.project.upload_document",
		disable_file_browser: 1,
		on_success(file_doc) {
			project_milestones.stages.load_documents(timeline, stage);
		}
	});
};

project_milestones.stages.approve_document = function(docname, document_name, timeline, stage) {
	return frappe.confirm(
		__('Are you sure you want to approve {0} Document {1}? This action may not be reversible.',
			[timeline, `<b>${document_name}</b>`]),
		function(){
			return frappe.call({
				method: "project_milestones.project_milestones.project.approve_document",
				args: {
					docname: docname
				},
				freeze: 1,
				always: function(r) {
					project_milestones.stages.load_documents(timeline, stage);
				}
			});
		},
	);
};

project_milestones.stages.request_review_document = function(docname, document_name, timeline, stage) {
	return frappe.confirm(
		__('Are you sure you want to request a review for {0} Document {1}?',
			[timeline, `<b>${document_name}</b>`]),
		function(){
			return frappe.call({
				method: "project_milestones.project_milestones.project.request_review_document",
				args: {
					docname: docname
				},
				freeze: 1,
				always: function(r) {
					project_milestones.stages.load_documents(timeline, stage);
				}
			});
		},
	);
};

project_milestones.stages.view_document = function(docname, fieldname) {
	const w = window.open("/api/method/project_milestones.project_milestones.project.download_document"
		+ "?docname=" + encodeURIComponent(docname)
		+ "&fieldname=" + encodeURIComponent(fieldname)
	);
	if(!w) {
		frappe.msgprint(__("Please enable pop-ups"));
	}
};

project_milestones.stages.set_document_client_view = function(docname, value, timeline, stage) {
	return frappe.call({
		method: "project_milestones.project_milestones.project.set_document_client_view",
		args: {
			docname: docname,
			value: cint(value)
		},
		freeze: 1,
		always: function(r) {
			project_milestones.stages.load_documents(timeline, stage);
		}
	});
};

// Handle stage button click
$(".stage-row").on('click', '.btn-stage', function () {
	const timeline = $(this).data('timeline');
	const stage = $(this).data('stage');
	project_milestones.stages.set_stage(timeline, stage);
});

// Load documents on DOM ready
$(document).ready(function () {
	$(`.btn-stage[data-selected='1']`).each(function (i, element) {
		const $btn = $(element);
		const timeline = $btn.data('timeline');
		const stage = $btn.data('stage');
		if (timeline && stage) {
			project_milestones.stages.load_documents(timeline, stage);
		}
	});
});
