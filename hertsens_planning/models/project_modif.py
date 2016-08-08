from openerp import models, fields, api
import pdb


class project(models.Model):
	_inherit="project.project"
	_description="Vehicles"
	vehicle_id=fields.Many2one('fleet.vehicle', string="Vehicle")
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")
	driver_id=fields.Many2one('res.users', string="Driver", track_visibility='onchange')
	free_for_planning=fields.Boolean(help="Is vehicle free for planning")
	origin=fields.Char(help="Current origin")
	destination=fields.Char(help="Current destination")
	false=fields.Boolean(help="fake field for searching logic", default=False)

	kanban_state=fields.Selection([('unavailable', 'Unavailabe'),('inuse', 'In Use'),('done', 'Available')], 'Kanban State',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Unavailabe/gray Unavailabe\n"
                                              " * In use/red, performing a ride\n"
                                              " * Available/green: Free for dispatch",
                                         required=False, copy=False, default='normal')

	@api.one	
	def write(self, vals=None):
		#pdb.set_trace()
		super(project,self).write(vals)

        
class task(models.Model):
	_inherit="project.task"

	ride_id=fields.Many2one('hertsens.rit', string="Ride")

	@api.one	
	def write(self, vals=None):

		if 'stage_id' in vals:
		 	new_stage=vals['stage_id']
		 	if new_stage==self.env['ir.model.data'].xmlid_lookup('project.project_tt_deployment')[2]:
		 		#new state=Ready
		 		self.end_ride()	
		 	if new_stage==self.env['ir.model.data'].xmlid_lookup('project.project_tt_cancel')[2]:
		 		#new state=Ready
		 		self.cancel_ride()		 	
		 	#if new_stage=self.env['ir.model.data'].xmlid_lookup('hertsens_planning.project_tt_exception')[3]:
	
		#project.project_tt_deployment
		#project.project_tt_cancel
		super(task,self).write(vals)

	@api.one
	def end_ride(self):
#		pdb.set_trace()		#process end of ride
		#update ride      
		self.ride_id.write({
			'finished':True,
			'state':'waiting',
			})
		#change vehicle status only if 1 ride assigned
		if self.project_id.task_count == 1:
			self.project_id.write({
				'kanban_state': 'done',
				'origin': '',
				#'destination': '',
				})
			self.user_id.write({
				'is_available_for_planning': True,
				})

	@api.one
	def cancel_ride(self):
#		pdb.set_trace()		#process end of ride
		#update ride      
		self.ride_id.write({
			'state':'planned',
			})
		#change vehicle status only if 1 ride assigned
		if self.project_id.task_count == 1:
			self.project_id.write({
				'kanban_state': 'done',
				'origin': '',
				'destination': '',
				})
			self.user_id.write({
				'is_available_for_planning': True,
				})
