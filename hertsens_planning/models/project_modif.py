from openerp import models, fields, api
import pdb


class project(models.Model):
	_inherit="project.project"
	
	vehicle_id=fields.Many2one('fleet.vehicle')
	vehicle_type_id=fields.Many2one('fleet.vehicle.type')
	driver_id=fields.Many2one('res.users')
	free_for_planning=fields.Boolean(help="Is vehicle free for planning")
	origin=fields.Char(help="Current origin")
	destination=fields.Char(help="Current destination")
	false=fields.Boolean(help="fake field for searching logic", default=False)

	kanban_state=fields.Selection([('normal', 'tbd'),('blocked', 'In Use'),('done', 'Available')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A task's kanban state indicates special situations affecting it:\n"
                                              " * Tbd/gray to define (Repair?)\n"
                                              " * In use/red, performing a ride\n"
                                              " * Available/green: Free for dispatch",
                                         required=False, copy=False, default='normal')

	@api.one	
	def write(self, vals=None):
		#pdb.set_trace()
		super(project,self).write(vals)

        
class task(models.Model):
	_inherit="project.task"
	ride_id=fields.Many2one('hertsens.rit')

	@api.one	
	def write(self, vals=None):

		if 'stage_id' in vals:
		 	new_stage=vals['stage_id']
		 	if new_stage==self.env['ir.model.data'].xmlid_lookup('project.project_tt_deployment')[2]:
		 		#new state=Ready
		 		self.end_ride()		 	
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

