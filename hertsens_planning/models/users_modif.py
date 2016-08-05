# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb


class res_users(models.Model):
	_inherit="res.users"
	is_driver=fields.Boolean(string="Driver", help="Tick if user is a driver")
	project_id=fields.Many2one('project.project', string="Current vehicle", help="Currently assigned vehicle")
