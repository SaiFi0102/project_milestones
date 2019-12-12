# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in project_milestones/__init__.py
from project_milestones import __version__ as version

setup(
	name='project_milestones',
	version=version,
	description='Project Timeline, Milestones and Portal',
	author='Saif Ur Rehman',
	author_email='saif@mocha.pk',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
