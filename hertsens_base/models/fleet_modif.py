# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb
import openerp
import logging

_logger = logging.getLogger(__name__)

class fleet_vehicle_type(models.Model):
	_name="fleet.vehicle.type"
	_description="Vehicle types"
	name=fields.Char(required=True)
	type_code=fields.Char(size=1, required=True)
	color_index=fields.Integer()
	vehicle_ids=fields.One2many('fleet.vehicle','vehicle_type_id')


	@api.one
	def name_get(self):
		name=self.name + " (" + self.type_code + ")"
		#pdb.set_trace()
		return self.id, name

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
		    recs = self.search([('type_code', 'ilike', name)] + args, limit=limit)
		if not recs:
		    recs = self.search([('name', operator, name)] + args, limit=limit)
		return recs.name_get()	

class fleet_vehicle(models.Model):
	_inherit="fleet.vehicle"
	_sql_constraints = {
	('vehicle_transics_id_uniq', 'unique(vehicle_transics_id)', 'Transics ID has to be unique')
    	}	
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type", required=True)
	vehicle_length=fields.Integer(string="Length", help="Vehicle heigth in cm")
	vehicle_width=fields.Integer(string="Width", help="Vehicle width in cm" )
	vehicle_heigth=fields.Integer(string="Heigth", help="Vehicle heigth in cm" )
	vehicle_load=fields.Integer(string="Load", help="Maximum load in kg")
	vehicle_pallets=fields.Integer(string="Pallet places", help="Number of pallet places")
	vehicle_license=fields.Char(string="License n°", help="License (Transport) number")
	project_id=fields.Many2one('project.project')
	vehicle_Transics_TransicsID=fields.Char(string='Transics ID', help='TransicsID of the vehicle (number)')
	vehicle_transics_id=fields.Char(string='TransicsID', help='ID of the vehicle (string)', oldname='vehicle_Transics_ID')


	@api.model
	def create(self, vals=None):
		new_vehicle=super(fleet_vehicle,self).create(vals)
		new_project=self.env['project.project'].create({
			'name': new_vehicle.license_plate ,
			'color': new_vehicle.vehicle_type_id.color_index,
			'vehicle_type_id': new_vehicle.vehicle_type_id.id,
			'vehicle_id': new_vehicle.id,			
			})
		new_vehicle.project_id=new_project.id
		return new_vehicle

	@api.multi
	def write(self,vals=None):

		if 'license_plate' in vals.keys():
			self.project_id.write({'name':self.license_plate})
		if 'vehicle_type_id' in vals.keys():
			self.project_id.write({'name':self.vehicle_type_id.id})
			
		return super(fleet_vehicle,self).write(vals)


	@api.multi
	def _migrate(self):
		_logger.info("Updating vehicle names..")

		records=self.env['fleet.vehicle'].search([])
		#pdb.set_trace()
		for record in records:
			record.project_id.write({'name': record.license_plate})
#			pdb.set_trace()


	def init(self,cr):
		#pdb.set_trace()
		self._migrate(cr, openerp.SUPERUSER_ID,[],{})


	# @api.one
	# def write(self,vals):
	# 	if not self.project_id.id:
	# 		pdb.set_trace()
	# 	else:
	# 		pdb.set_trace()
	#  	super(fleet_vehicle,self).write(vals)




