frappe.ui.form.on("Project", {
	get_stages_from_project_type: function(frm) {
		if (frm.doc.project_type) {
			frappe.call({
				method: 'project_milestones.project_milestones.project.get_stages_from_project_type',
				args: {
					project_type: frm.doc.project_type
				},
				callback: function (r) {
					if (r) {
						frm.clear_table("stages");
						$.each(r.message || [], function (i, d) {
							frm.add_child("stages", d);
						});
						frm.refresh_field("stages");
					}
				}
			});
		} else {
			frappe.throw(__("Please select Project Type first"));
		}
	},
	get_documents_from_stages: function(frm) {
		if (frm.doc.stages && frm.doc.stages.length) {
			frappe.call({
				method: 'project_milestones.project_milestones.project.get_documents_from_project_stages',
				args: {
					project_stages: frm.doc.stages
				},
				callback: function (r) {
					if (r) {
						frm.clear_table("documents");
						$.each(r.message || [], function (i, d) {
							frm.add_child("documents", d);
						});
						frm.refresh_field("documents");
					}
				}
			});
		} else {
			frappe.throw(__("Please select Project Stages first"));
		}
	}
});
