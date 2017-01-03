# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb
import openerp
import logging
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class hertsens_rit(models.Model):
	_inherit="hertsens.rit"
	_sql_constraints = {
    ('last_msg_uniq', 'unique(last_msg)', 'Last msg is niet uniek. Luc Bonjean verwittigen aub')
    }
	vehicle_type_id=fields.Many2one('fleet.vehicle.type', string="Vehicle type")
	task_ids=fields.One2many('project.task','ride_id')
#	driver_id=fields.Many2one('res.users')
	driver_id=fields.Many2one('hr.employee')
	vehicle_id=fields.Many2one("fleet.vehicle")
	last_msg=fields.Char()
	last_msg_display=fields.Char(compute='_compute_last_msg_display', string="Last msg", help="Naar wie is de laatste sms gestuurd.")


	@api.depends('last_msg')
	def _compute_last_msg_display(self):
		for rec in self:
			rec.last_msg_display=rec.last_msg


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

	@api.onchange('finished')
	def _empty_last_msg(self):
		if self.finished:
			self.last_msg=None

	def init(self,cr):
		self._migrate(cr, openerp.SUPERUSER_ID,[],{})
		# cr.execute("SELECT id, datum, departure_time FROM hertsens_rit"
  #       	     " WHERE departure_time IS NULL")
		# for datum, departure_time 
		#pdb.set_trace()
	@api.multi
	def dispatch_ride(self):
		#dispatch the ride with sms
		#self.last_msg=self.driver_id.mobile_phone
		if not self.driver_id:
			raise ValidationError("Chauffeur moet ingevuld zijn!")
		else:
			return {
                 'name': 'Individual SMS Compose',
                 'view_type': 'form',
                 'view_mode': 'form',
                 'res_model': 'esms.compose',
                 'target': 'new',
                 'type': 'ir.actions.act_window',
#                 'context': {'default_field_id':'mobile','default_to_number':self.driver_id.mobile_phone, 'default_record_id':self.env.context['active_id'],'default_model_id':'res.partner'}
                 'context': {'default_field_id':'mobile','default_to_number':self.driver_id.mobile_phone ,'default_model_id':'hertsens.rit','default_record_id':self.id , 'default_template_id':1}
            	}
	@api.multi
	def dispatch_ride_silent(self):
		#dispatch the ride without sms
		#self.last_msg=self.driver_id.mobile_phone
		if not self.driver_id:
			raise ValidationError("Chauffeur moet ingevuld zijn!")
		else:
			self.set_last_msg(self.driver_id.mobile_phone,"Manueel toegewezen")

	@api.multi		
	def clr_last_msg(self):
		self.sudo().last_msg=None
		self.sudo().message_post(body="",
			subject="Last msg manueel gecleared",
			type = 'comment',
 			#subtype = "mail.mt_comment"
		)
			


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
            }

	@api.multi
	def set_last_msg(self,to_number,body):
		mobile_e164=calc_e164(to_number)
		last_ride=self.search([('last_msg','=',mobile_e164)])
		for rit in last_ride:
			rit.sudo().last_msg=""
		#pdb.set_trace()
		self.last_msg=mobile_e164
		self.message_post(body=body,
			subject="Rit: " + str(self.id) + "," + self.display_name + " Drv: " + self.driver_id.name,
			type = 'comment',
 			#subtype = "mail.mt_comment"
		)
		self.message_subscribe_users(user_ids=62)



def calc_e164(number,country="32"):
    mobile_e164=""
    if number.startswith("00"):
        mobile_e164 = "+" + number[2:]
    elif number.startswith("0"):
        mobile_e164 = "+" + country + number[1:]
    elif number.startswith("+"):
        mobile_e164 = number
    else:
        mobile_e164 = "+" + country + number
    return mobile_e164

