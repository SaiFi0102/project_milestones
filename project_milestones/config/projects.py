from __future__ import unicode_literals
from frappe import _


def get_data():
	return [
		{
			"label": _("Project Milestones"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Project Milestones Settings",
					"settings": 1,
					"description": _("Default Project Milestones Settings."),
				},
				{
					"type": "doctype",
					"name": "Project Timeline",
					"description": _("Define Project Timeline Category."),
				},
				{
					"type": "doctype",
					"name": "Project Stage",
					"description": _("Define Project Stage."),
				},
			]
		}
	]
