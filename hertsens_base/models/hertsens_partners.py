# -*- coding: utf-8 -*-
#from openerp.osv import osv
from openerp import exceptions,models, fields, api, _
import csv,os,string,pdb
#from path import path
from datetime import date,datetime,timedelta
from pytz import timezone
import time
import logging
import pytz,base64
from zeep import Client
from openerp.exceptions import except_orm, Warning, RedirectWarning

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
	_inherit= ['res.partner']

 	mail_invoice = fields.Char(string="Invoice e-mail", help="e-mail adress used to send invoices")
 	mail_reminder = fields.Char(string="Reminder e-mail", help="e-mail used to send reminders")
 	mail_planning = fields.Char(string="Planning e-mail", help="e-mail used for planning")
 	on=fields.Char(default="on")
	ref_required=fields.Boolean(string="Ref required",help="Customer reference mandatory?")
	diesel=fields.Float(help="Dieseltoeslag")
	ritten_count=fields.Float(compute="_ritten_count")
	#partner_id=fields.Many2one('res.partner', required=True)
	ride_ids=fields.One2many('hertsens.rit','partner_id')
	geo_longitude=fields.Float(String="Longitude (X)", digits=(16, 5))
	geo_latitude=fields.Float(String="Latitude (Y)",digits=(16, 5))
	geo_name=fields.Char()
	geo_ok=fields.Boolean(help='Geo of place is found, not modifiable')
	geo_google_maps_url=fields.Char(compute='_compute_geo_google_maps_url')
#	display_name = fields.Char(string='Name', compute='_display_name_compute2')
	type=fields.Selection(selection_add=[('place','Place')])


	@api.depends('geo_latitude','geo_longitude')
	def _compute_geo_google_maps_url(self):
		for record in self:
			if record.geo_latitude and record.geo_longitude:
				record.geo_google_maps_url='https://www.google.com/maps/search/?api=1&query=' + str(record.geo_latitude) + ','+ str(record.geo_longitude)

	@api.multi
	def get_geo(self):
		response=self.env['transics.transics'].Get_PositionFromStreetInfo(City=self.city,PostalCode=self.zip,Street=self.street,CountryCode=self.country_id.code_alpha3,)

		self.geo_name=response['Position']['Name']
		self.geo_latitude=response['Position']['Latitude']
		self.geo_longitude=response['Position']['Longitude']

		if self.geo_name and len(self.geo_name)>0:
			self.geo_ok=False #True
		else:
			self.geo_ok=False
			self.geo_name=None
			self.geo_latitude=0
			self.geo_longitude=0		
			raise Warning (_('No location found'))
		#pdb.set_trace()

	@api.one
	def get_geoXY_string(self):
		if self.geo_latitude and self.geo_longitude:
			return str(self.geo_latitude) + ',' + str(self.geo_longitude)
		else:
			return ''

	@api.one
	def _ritten_count(self):
		self.ritten_count=0
		for f in self.ride_ids:
			self.ritten_count=self.ritten_count+1
		return 

	@api.multi	
	def name_get(self,context=None):
		show_address_line=True	
		for partner in self:
			if partner.type and partner.type != 'place':
				show_address_line=False
				break

		if show_address_line or ('show_address_line' in self.env.context.keys()):
			#pdb.set_trace()
			res=[]
			for partner in self:
				name=partner.name  
			#	if partner.type == "place":
			#		pdb.set_trace()
				if partner.street:
					name += ", " + partner.street
				if partner.zip:
					name += ", " + partner.zip
				if partner.city:
					name += ", " + partner.city
				if partner.country_id:
					name +=  " (" + partner.country_id.code +")"

				res.append((partner.id,name))
			#pdb.set_trace()	
		else:
			res=super(res_partner, self).name_get()
		return res

	@api.one
	@api.depends('name', 'parent_id.name')
	def _display_name_compute2(self,name,args):
		#pdb.set_trace()
		if 'show_address_line' in self.env.context.keys():
			res=[]
			for partner in self:
				name=partner.name  
				if partner.street:
					name += ", " + partner.street
				if partner.zip:
					name += ", " + partner.zip
				if partner.city:
					name += ", " + partner.city
				if partner.country_id:
					name +=  " (" + partner.country_id.code +")"
				res.append((partner.id,name))
		else:
			res=super(res_partner, self)._display_name_compute(name, args)
		#pdb.set_trace()
		return res

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100 ):
		if 'show_address_line' in self.env.context.keys():
			args = args or []
			recs = self.browse()
			name_arr=name.split(" ")

			for n in name_arr:
				#pdb.set_trace()
				r=None
				if len(n)>0:
					r=self.search([('zip', 'ilike', n)])
					r=r + self.search([('street', 'ilike', n)])
					r=r + self.search([('name', 'ilike', n)])
					r= r & self.search(args)
				if not recs:
					recs=r	
				if r:
					recs=recs & r


#			if name:
#				recs = self.search(['|','|',('street', 'ilike', name),('city', 'ilike', name),('zip', 'ilike', name)] + args, limit=limit)
			if not recs:
				recs = self.search([('name', operator, name)] + args, limit=limit)
			return recs.name_get()
		else:
			return super(res_partner, self).name_search(name=name, args=args,operator=operator, limit=limit)
