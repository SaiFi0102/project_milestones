# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "project_milestones"
app_title = "Project Milestones"
app_publisher = "Saif Ur Rehman"
app_description = "Project Timeline, Milestones and Portal"
app_icon = "fa fa-tasks"
app_color = "blue"
app_email = "saif@mocha.pk"
app_license = "MIT"

doctype_js = {
	"Project": "public/js/project.js"
}

doc_events = {
	"Project": {
		"validate": "project_milestones.project_milestones.project.validate",
		"onload": "project_milestones.project_milestones.project.onload"
	},
	"Project Type": {
		"validate": "project_milestones.project_milestones.project_type.validate",
	},
	"Purchase Order": {
		"on_submit": "project_milestones.project_milestones.project.on_po_submit_cancel",
		"on_cancel": "project_milestones.project_milestones.project.on_po_submit_cancel",
	},
	"Payment Entry": {
		"on_submit": "project_milestones.project_milestones.project.on_pe_submit_cancel",
		"on_cancel": "project_milestones.project_milestones.project.on_pe_submit_cancel",
	},
	"Journal Entry": {
		"on_submit": "project_milestones.project_milestones.project.on_jv_submit_cancel",
		"on_cancel": "project_milestones.project_milestones.project.on_jv_submit_cancel",
	}
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/project_milestones/css/project_milestones.css"
# app_include_js = "/assets/project_milestones/js/project_milestones.js"

# include js, css files in header of web template
# web_include_css = "/assets/project_milestones/css/project_milestones.css"
# web_include_js = "/assets/project_milestones/js/project_milestones.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "project_milestones.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "project_milestones.install.before_install"
# after_install = "project_milestones.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "project_milestones.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"project_milestones.tasks.all"
# 	],
# 	"daily": [
# 		"project_milestones.tasks.daily"
# 	],
# 	"hourly": [
# 		"project_milestones.tasks.hourly"
# 	],
# 	"weekly": [
# 		"project_milestones.tasks.weekly"
# 	]
# 	"monthly": [
# 		"project_milestones.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "project_milestones.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "project_milestones.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "project_milestones.task.get_dashboard_data"
# }

