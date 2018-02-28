# -*- coding: utf-8 -*-

from openerp import models, fields, api,_

import pdb

class planning_transics_wizard(models.TransientModel):
	_name = "planning.transics.wizard"
#	ride_ids=fields.Many2many('hertsens.rit')

	vehicle_id=fields.Many2one('fleet.vehicle')
	show_type_only=fields.Boolean(help="Show only vehicles of this type", default=True)
	show_free_only=fields.Boolean(help="Show only free vehicles", default=True)
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")	
	

	dispatch_message=fields.Text()

	@api.model
	def create(self, vals=None):
		wiz=super(planning_transics_wizard,self).create(vals)
		return wiz

	def _default_rides(self):
		#pdb.set_trace()
		return self._context.get('active_ids')
	ride_ids=fields.Many2many('hertsens.rit', default=_default_rides)

	destination_ids=fields.One2many('planning.transics.destination', 'wizard_id')


	def _get_destinations(self,ride_ids):
		res=[]	
		n=10
		for ride in ride_ids:
			for dest in ride.destination_ids:
				n+=10
				new=self.env['planning.transics.destination'].create({
					'destination_id': dest.id,
					'sequence':n,
					'name':dest.place_id.display_name,
					'ref':dest.ref,
					'remarks':dest.remarks,
					'state':dest.state,
					'activity':dest.activity_id,
					'ride_id':dest.rit_id.id,
					'wizard_id':self.id,
					})
				if new.state in ['planned','cancelled']:
					new.dispatch=True
				res.append(new.id)
		return res		
	@api.multi	
	def confirm_dispatch(self):
		#pdb.set_trace()
		for dest in self.destination_ids.sorted(key=lambda l: l.sequence):
			if dest.dispatch:
				self.env['hertsens.destination.hist'].create_transics_planning(dest.destination_id,self.vehicle_id,dest.ref,dest.remarks,self.id)
				
		#if dest:
		#	self.env['transics.transics'].dispatcher_query()

class planning_transics_destination(models.TransientModel):
	_name = "planning.transics.destination"
	_order="sequence,id"

	destination_id=fields.Many2one('hertsens.destination' )
	sequence=fields.Integer()
	name=fields.Char()
	ref=fields.Char()
	remarks=fields.Char()
	state=fields.Char()
	dispatch=fields.Boolean()
	ride_id=fields.Integer()
	activity=fields.Char()
	wizard_id=fields.Many2one('planning.transics.wizard')




