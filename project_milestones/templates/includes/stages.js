frappe.provide("project_milestones.stages");

project_milestones.stages.set_stage = function(timeline, stage) {
	if (!timeline || !stage) {
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

	frappe.call({
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
		const style = $(th).attr('style');
		const classStr = $(th).attr('class');

		if (fieldname) {
			field_list.push({fieldname: fieldname, fieldtype: fieldtype, style: style, class: classStr});
		}
	});

	return field_list;
};

// Make table field name
project_milestones.make_table_field = function(field, doc) {
	let $value;
	const value = doc[field.fieldname];

	if (field.fieldtype === "Check") {
		$value = $(`<input type="checkbox" value="${cint(value)}" disabled="disabled" />`)
	} else if(field.fieldtype === "Attach") {
		$value = $(`<button type="button" class="btn btn-primary btn-sm"></button>`);

		let label = value ? "View" : "Attach";
		$value.text(label);

		if (value) {
			$value.click(() => project_milestones.stages.view_document(doc.name, field.fieldname));
		} else {
			$value.click(() => project_milestones.stages.attach_document(doc.name, field.fieldname,
				doc.project_timeline, doc.project_stage));
		}
	} else if (field.fieldtype === "Date") {
		const formatted_date = frappe.format(value, {fieldtype: "Date"});
		$value = $(`<div></div>`);
		$value.text(formatted_date);
	} else {
		$value = $(`<div></div>`);
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

project_milestones.stages.view_document = function(docname, fieldname) {
	var w = window.open("/api/method/project_milestones.project_milestones.project.download_document"
		+ "?docname=" + encodeURIComponent(docname)
		+ "&fieldname=" + encodeURIComponent(fieldname)
	);
	if(!w) {
		frappe.msgprint(__("Please enable pop-ups"));
	}
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
