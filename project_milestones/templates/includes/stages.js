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
						$td.append(project_milestones.make_table_field(field, document[field.fieldname]));

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
project_milestones.make_table_field = function(field, value) {
	let $value;

	if (field.fieldtype === "Check") {
		$value = $(`<input type="checkbox" value="${cint(value)}" disabled="disabled" />`)
	} else {
		$value = $(`<div></div>`);
		$value.text(cstr(value));
	}

	return $value;
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