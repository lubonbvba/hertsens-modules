# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb
import openerp
import logging

_logger = logging.getLogger(__name__)

class hertsens_rit(models.Model):
	_inherit="hertsens.rit"

	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")
	task_ids=fields.One2many('project.task','ride_id')
	
	@api.one
	def name_get(self):
		name=(self.vertrek or "") + " - " + (self.bestemming or "")
#		pdb.set_trace()
		if 'detailed' in self.env.context.keys():
			pdb.set_trace()

		return self.id, name		

	@api.multi
	def _migrate(self):
		_logger.info("Updating departure_times...")

		records=self.search([('departure_time','=', False)])
		for record in records:
			record.departure_time=self._calculate_departure_time(record.datum)
#			pdb.set_trace()


	def init(self,cr):
		self._migrate(cr, openerp.SUPERUSER_ID,[],{})
		# cr.execute("SELECT id, datum, departure_time FROM hertsens_rit"
  #       	     " WHERE departure_time IS NULL")
		# for datum, departure_time 
		#pdb.set_trace()


	@api.multi	
	def dispatch_wizard(self):
		#pdb.set_trace()
		wiz=self.env['vehicle.planning.wizard'].create({
			'ride_id':self.id,
#			'name': self.name_get(),
			'vehicle_type_id': self.vehicle_type_id.id,
			'partner_id': self.partner_id.id,
			})

		return {
                'name': 'Dispatch Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vehicle.planning.wizard',
                'domain': [],
                'context': self.env.context,
                'res_id': wiz.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
#                'nodestroy': True,
            }



