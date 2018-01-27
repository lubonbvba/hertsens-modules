from openerp import models, fields, api
import pdb


class employee(models.Model):
	_inherit="hr.employee"
	_sql_constraints = {
	('transics_id_uniq', 'unique(transics_id)', 'Transics ID has to be unique')
    	}
	tasks_ids=fields.One2many('project.task', 'employee_id')
	transics_id=fields.Char(help='String')