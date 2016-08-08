# -*- coding: utf-8 -*-

from openerp import models, fields, api,_

import pdb


class vehicle_planning_wizard(models.TransientModel):
	_name="vehicle.planning.wizard"
	ride_id=fields.Many2one('hertsens.rit', string="ride")
	project_id=fields.Many2one('project.project', string="Vehicle")
	partner_id=fields.Many2one('res.partner', string="Customer")
	task_id=fields.Many2many('project.task')
	driver_id=fields.Many2one('res.users', string="Driver")
	name=fields.Char()
	dispatch_message=fields.Text()
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")
	show_type_only=fields.Boolean(help="Show only vehicles of this type", default=True)
	show_free_only=fields.Boolean(help="Show only free vehicles", default=True)
	planning_vehicles_ids=fields.One2many('planning.vehicles','vehicle_planning_wizard_id')

	@api.model
	def create(self, vals=None):
		wiz=super(vehicle_planning_wizard,self).create(vals)
		wiz.set_candidates()
		return wiz




	@api.multi
	@api.depends('show_type_only','show_free_only')
	def set_candidates(self):
		for candidate in self.planning_vehicles_ids:
			candidate.unlink()
		candidates=self.env['project.project'].search(['&','|',('vehicle_type_id','=',self.vehicle_type_id.id),('false',"=",self.show_type_only),'|',('kanban_state','=','done'),('false',"=",self.show_free_only)])	
		self.env['planning.vehicles'].new_candidates(self,candidates)	
		return {
                'name': 'Dispatch Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vehicle.planning.wizard',
                'domain': [],
                'context': self.env.context,
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
#                'nodestroy': True,
            }


  
class planning_vehicles(models.TransientModel):
	_name="planning.vehicles"
	_description="Available vehicles"

	vehicle_planning_wizard_id=fields.Many2one("vehicle.planning.wizard")
	name=fields.Char()
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")
	project_id=fields.Many2one('project.project', string="Vehicle")
	partner_id=fields.Many2one('res.partner', string="Customer")
	
	driver_id=fields.Many2one('res.users', string="Driver")	
	kanban_state=fields.Selection([('unavailable', 'Unavailabe'),('inuse', 'In Use'),('done', 'Available')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Tbd/gray to define (Repair?)\n"
                                              " * In use/red, performing a ride\n"
                                              " * Available/green: Free for dispatch",
                                         required=False, copy=False, default='normal')

	@api.multi
	def new_candidates(self,wizard,candidates):
#		pdb.set_trace()
		for candidate in candidates:
			self.create({
				'name':candidate.name,
				'kanban_state': candidate.kanban_state,
				'vehicle_type_id': candidate.vehicle_type_id.id,
				'vehicle_planning_wizard_id':wizard.id,
				'project_id':candidate.id,
				'driver_id':candidate.driver_id.id,
			})

	@api.multi
	def select_candidate(self):
		dispatch_wizard=self.env['vehicle.dispatch.wizard'].create({
			'ride_id': self.vehicle_planning_wizard_id.ride_id.id,
			'project_id': self.project_id.id,
			'driver_id': self.project_id.driver_id.id,
			'dispatch_message': "V: %s\nVan: %s\nNaar: %s\nOK?" % (self.project_id.name, self.vehicle_planning_wizard_id.ride_id.vertrek,self.vehicle_planning_wizard_id.ride_id.bestemming),
			})
		dispatch_wizard.driver_mobile=str(self.project_id.driver_id.employee_ids.mobile_phone)
		dispatch_wizard.partner_id=dispatch_wizard.ride_id.partner_id
		return {
               'name': 'Dispatch Wizard',
               'view_type': 'form',
               'view_mode': 'form',
               'res_model': 'vehicle.dispatch.wizard',
               'domain': [],
               'context': self.env.context,
               'res_id': dispatch_wizard.id,
               'type': 'ir.actions.act_window',
               'target': 'new',
#               'nodestroy': True,
            }



class vehicle_dispatch_wizard(models.TransientModel):
	_name='vehicle.dispatch.wizard'
	ride_id=fields.Many2one('hertsens.rit',required=True, string="Ride")
	project_id=fields.Many2one('project.project', required=True, string="Vehicle")
	driver_id=fields.Many2one('res.users', string="Driver")
	driver_mobile=fields.Char()
	dispatch_message=fields.Text(size=160)
	partner_id=fields.Many2one('res.partner', string="Customer")

	@api.onchange('driver_id')
	@api.one
	def change_mobile(self):
		#pdb.set_trace()
		self.driver_mobile = self.driver_id.employee_ids.mobile_phone

	@api.multi
	def confirm_dispatch(self):
		#pdb.set_trace()
		#check if driver changed on vehicle
		if self.driver_id != self.project_id.driver_id:
			#remove vehicle from driver
			self.project_id.driver_id.write({
					'project_id':False,
					'is_availabe_for_planning':True,
				})
			#remove driver from project
			self.driver_id.project_id.write(
				{
					'driver_id':False,
					'members':[[3,self.driver_id.id]],
				})
			#update driver
			self.driver_id.write(
				{
				'project_id':self.project_id.id,
				'is_availabe_for_planning':True,
				})
		else:
			self.driver_id.write(
				{
				'project_id':self.project_id.id,
				'is_availabe_for_planning':False,
				})			
		#update project with new ride	
		self.project_id.write({
			'driver_id':self.driver_id.id,
			'origin': self.ride_id.vertrek,
			'destination':self.ride_id.bestemming,
			'kanban_state':'inuse',
			'members':[[6, False, [self.driver_id.id]]],
			})
		#update ride status
		self.ride_id.write({
			'state':'dispatched',
			})
		#create task
		self.env['project.task'].create({
			'name': self.ride_id.name_get()[0][1].encode("utf8"),
			'project_id': self.project_id.id,
			'user_id': self.driver_id.id,
			'ride_id':self.ride_id.id,	
			'description': self.dispatch_message,	
			})

