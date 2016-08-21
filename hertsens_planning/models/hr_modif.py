from openerp import models, fields, api
import pdb


class employee(models.Model):
	_inherit="hr.employee"
	tasks_ids=fields.One2many('project.task', 'employee_id')