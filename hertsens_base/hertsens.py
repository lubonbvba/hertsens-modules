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

_logger = logging.getLogger(__name__)
# class account_analytic_line(models.Model):
# 	_inherit= "account.analytic.line"

# 	cmr=fields.Char(help="CMR Nummer")
# 	datum=fields.Date()
# 	wachttijd=fields.Float(help="Prijs wachttijd")
# 	ritprijs=fields.Float()
# 	vertrek=fields.Char(help="Vertrek plaats")
# 	bestemming=fields.Char(help="Bestemming plaats")
# 	refklant=fields.Char(help="Referentie opvegegeven door klant")	


class hertsens_rit(models.Model):
	_name="hertsens.rit"
	_inherit="mail.thread"
#	_inherits= {"account.analytic.line":"line_id"}
	_order = "datum desc"

#	line_id=fields.Many2one('account.analytic.line', required=True, ondelete="cascade")
	partner_id=fields.Many2one('res.partner', string="Customer", required=True)
	company_id=	fields.Many2one( 'res.company', string="Company", required=True)
	cmr=fields.Char(string="CMR", help="CMR Nummer")
	datum=fields.Date(help="Aflever datum", copy=False)
	departure_time=fields.Datetime(help="Vertrek datum/tijd")
	define_departure_time=fields.Boolean(string='VL', help="Voorladen")
	wachttijd=fields.Float(help="Prijs wachttijd")
	ritprijs=fields.Float()
	remarks=fields.Text(help="Info om mee te sturen bij dispatch")
	vertrek=fields.Char(help="Vertrek plaats")
	bestemming=fields.Char(help="Bestemming plaats")
	refklant=fields.Char(string="Ref", help="Referentie opgegeven door klant")
	charges_vat=fields.Float(help="Reimbursements vat")
	charges_exvat=fields.Float(help="Reimbursements vat exempt")
	invoice_id=fields.Many2one('account.invoice')
	destination_ids=fields.One2many('hertsens.destination','rit_id')
	finished=fields.Boolean(help="Tick if ride is finished")
	state=fields.Selection([('quoted','Quote'),('planned','Planned'),('dispatched','Dispatched'),('cancelled', 'Cancelled'),('completed','Completed'),('waiting','Waiting for info'),('toinvoice','To be invoiced'),('invoiced','Invoiced')], required=True, default='planned')
	on=fields.Char(required=True,default="on")
	is_recurring=fields.Boolean(help="Tick if recurring", copy=False)
	recurring_active=fields.Boolean(help="Is active?", copy=False)
	recurring_start_date=fields.Date(help="Recurring start", copy=False)
	recurring_end_date=fields.Date(help="Recurring end date", copy=False)
	recurring_departure_time=fields.Char(default="23:59", help="Dispatch time in 24hrs format",copy=False)
	recurring_interval=fields.Integer(default=7,copy=False)
	recurring_interval_type=fields.Selection([('days','Days')], default='days',copy=False)
	recurring_offset=fields.Integer(default=7,help="Number of days before the departure time to make the dispatch record", copy=False)
	recurring_next_date=fields.Date(string='Next ride to be planned', help="Next planned date",copy=False)	
	recurring_active_days=fields.Many2many('hertsens.dow')
	parent_id=fields.Many2one('hertsens.rit', copy=False)
	child_ids=fields.One2many('hertsens.rit', 'parent_id')
	vehicle_id=fields.Many2one('fleet.vehicle', copy=False)
	driver_id=fields.Many2one('hr.employee')
#	origin_partner_id=fields.Many2one('res.partner', string="Origin")
#	destination_partner_id=fields.Many2one('res.partner', string="Destination")
	google_navigation_url=fields.Char(string='Google Nav', compute='_compute_google_navigation_url')
	# @api.onchange('partner_id')
	# def _checkcompany(self):
	# 	self.company_id=self.partner_id.company_id
	# @api.multi
	# def unlink(self):
	# 	pdb.set_trace()
	# 	for ride in self:
	# 		if ride.state not in ('draft', 'cancel'):
	# 			raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
	# 			return models.Model.unlink(self)





	@api.one
	@api.onchange('ritprijs','wachttijd')
	def _calculate_total(self):
		self.total_ride_price=self.ritprijs + self.wachttijd

	total_ride_price=fields.Float(string="Total price", compute=_calculate_total)

	@api.one
	@api.onchange('partner_id')
	def _set_company(self):
		self.company_id=self.partner_id.company_id
	

	@api.multi
	def _calculate_departure_time(self,datum):
		if datum:
				return datum + ' 21:59:00'
		else:
				return False
#		pdb.set_trace()	

	@api.multi
	@api.onchange('is_recurring')
	def _set_recurring(self):
		if self.is_recurring:
			self.state='dispatched'



	@api.one	
	def write(self, vals=None):
		#pdb.set_trace()
		if 'datum' in vals.keys():
			vals['departure_time']=self._calculate_departure_time(vals['datum'])
#		if 'remarks' in vals.keys():


			
	

		super(hertsens_rit,self).write(vals)

	@api.model
	def create(self, vals):
		#pdb.set_trace()
		if not 'departure_time' in vals.keys():
			vals['departure_time']=self._calculate_departure_time(vals['datum'])
		return super(hertsens_rit,self).create(vals)



	@api.one
	@api.onchange('finished','refklant','ritprijs', 'datum','cmr')
	def _checkstate(self):
		flagvalid=True
		if self.ritprijs==0:
			flagvalid=False
		if not self.cmr:
			flagvalid=False
		if self.partner_id.ref_required and not self.refklant:
			flagvalid=False
		if self.finished:
			if flagvalid:
				self.state='toinvoice'
			else:
				self.state='waiting'
		else:
			if fields.Date.context_today(self)>self.datum:
				self.state='completed'
			else:
				self.state='planned'
	@api.one			
	@api.depends('destination_ids')			
	def _compute_google_navigation_url(self):			
		destinations=self.destination_ids.sorted(key=lambda l: l.sequence)
		nr_dest=len(destinations)
		self.google_navigation_url="https://www.google.com/maps/dir/?api=1"
		if nr_dest>=2:
			#pdb.set_trace()
			self.google_navigation_url+="&origin="+ destinations[0].place_id.get_geoXY_string()[0]
			self.google_navigation_url+="&destination="+ destinations[nr_dest-1].place_id.get_geoXY_string()[0]
			if nr_dest>2:
				self.google_navigation_url+="&waypoints="
				nvia=0
				for via in range(1,nr_dest-1):
					self.google_navigation_url+= destinations[via].place_id.get_geoXY_string()[0] + "|"
	@api.one				
	def create_transics_planning(self):				
		destinations=self.destination_ids.sorted(key=lambda l: l.sequence)
		places=[]
		nseq=10
#		planninginsert= {'Vehicle':{'IdentifierVehicleType':'ID','Id':'DEMO_LUBON' }}
		planninginsert= {'Vehicle':{'IdentifierVehicleType':'ID','Id':self.vehicle_id.vehicle_Transics_ID }}
		for place in destinations:
			placesinsert={
				'OrderSeq':nseq,
				'PlaceId':str(self.id) + '_' + str(place.id),
				'DriverDisplay': ('ID:' + ' ' + str(place.rit_id.id ) + ',('+ place.place_id.country_id.code + ') ' + place.place_id.geo_name)[:50],
				'Comment':  place.place_id.name + ", " + place.place_id.geo_name,  
#				'ExecutionDate': '2017-12-04T18:00:00',
				'Activity':{},
#				'AlarmTimeETA':'True',
#				'CustomNr':'True',
				'Position':{'Longitude':place.place_id.geo_longitude,'Latitude':place.place_id.geo_longitude},
#				'SalesPrice':'True'
			}
			#Set activity field
			if place.activity_id == 'load':
				placesinsert['Activity']['ID']=self.env['ir.config_parameter'].get_param('transics.act_load_id', '')
			if place.activity_id == 'unload':
				placesinsert['Activity']['ID']=self.env['ir.config_parameter'].get_param('transics.act_unload_id', '')
			#Complet Comment field	
			if place.ref:	
				placesinsert['Comment']	+= '\nRef: ' + place.ref
			if place.remarks:	
				placesinsert['Comment']	+= '\n' +	place.remarks 
			nseq+=10
			places.append(placesinsert)
		planninginsert['Places']={'PlaceInsert':places}
		#pdb.set_trace()
		response=self.env['transics.transics'].Insert_Planning(planninginsert)

	@api.one				
	def cancel_transics_planning(self):				
		destinations=self.destination_ids.sorted(key=lambda l: l.sequence)
		for place in destinations:
			place.cancel_transics_planning()
			self.state='cancelled'






	@api.multi
	def _prepare_cost_invoice(self, partner_id):
		invoice_name = self.partner_id.name
		return {
        'name': "%s - %s" % (time.strftime('%d/%m/%Y'), invoice_name),
        'partner_id': partner_id,
        'company_id': self.company_id,
        'payment_term': self.partner_id.property_payment_term.id or False,
        'account_id': self.partner_id.property_account_receivable.id,
		#            'currency_id': currency_id,
		#            'date_due': date_due,
		'fiscal_position': self.partner_id.property_account_position.id
		}

	@api.multi
	def check_recurrent_rides(self,dummy=None):
		_logger.info('Start recurrent rides planner')
		rides = self.search([('is_recurring',"=",True),('recurring_active',"=",True)])
		for ride in rides:
			_logger.info('Processing ride: %d' % ride.id)
			if not ride.recurring_next_date:
				ride.recurring_next_date=ride.recurring_start_date
			while (
				((not ride.recurring_end_date) or (ride.recurring_next_date <= ride.recurring_end_date)) 
				 and (datetime.strptime(ride.recurring_next_date,"%Y-%m-%d") - datetime.now()) < timedelta(days=ride.recurring_offset)
				 ):
#				t=datetime.strptime(ride.recurring_next_date + " " + ride.recurring_departure_time,"%Y-%m-%d %H:%M")
#				timez=timezone(self.env.context['tz'])
				new=ride.copy({
#					'datum': ride.recurring_next_date,
#					'departure_time': ride.recurring_next_date + " " + ride.recurring_departure_time,
					'parent_id': ride.id,
					'state': 'planned',
					'last_msg': None,
					'driver_id':None,
					})
				new.datum=ride.recurring_next_date
				#pdb.set_trace()
				for destination in ride.destination_ids:
					newdest=destination.copy({
						'rit_id':new.id,
						'vehicle_id':None,
						})
				if ride.recurring_interval != 1:
					ride.recurring_next_date=time.strftime("%Y-%m-%d", (datetime.strptime(ride.recurring_next_date,"%Y-%m-%d") + timedelta(days=ride.recurring_interval)).timetuple())
				else:
					days=[]
					#create list with days the ride needs to be executed
					for day in ride.recurring_active_days:
						days.append(day.day_number)
					next_date=datetime.strptime(ride.recurring_next_date,"%Y-%m-%d")
					next_date +=timedelta(days=ride.recurring_interval)
					while next_date.isoweekday() not in days:
						next_date +=timedelta(days=ride.recurring_interval)
					ride.recurring_next_date=time.strftime("%Y-%m-%d", next_date.timetuple())	
		_logger.info('End recurrent rides planner')					







	@api.multi
	def invoice_cost_create(self, data):
		invoice_grouping = {}
		invoices = []

		for line in self:
		    key = (line.company_id.id,
		           line.partner_id.id)
		    invoice_grouping.setdefault(key, []).append(line)
		for (company_id, partner_id), rides in invoice_grouping.items():
		#	curr_invoice = self._prepare_cost_invoice(partner_id)
			#pdb.set_trace()
			ride=rides[0]
			curr_invoice = {
			'name': "%s - %s" % (time.strftime('%d/%m/%Y'), ride.partner_id.name),
        	'partner_id': ride.partner_id.id,
        	'company_id': ride.company_id.id,
        	'payment_term': ride.partner_id.property_payment_term.id or False,
        	'date': data['date'],
        	'account_id': ride.partner_id.property_account_receivable.id,
		#            'currency_id': currency_id,
		#            'date_due': date_due,
			'fiscal_position': ride.partner_id.property_account_position.id,
			'reference_type:': ride.partner_id.out_inv_comm_type
			}
			#pdb.set_trace()
			new_invoice=self.env['account.invoice'].create(curr_invoice)
			invoices.append(new_invoice.id)
			ntotal=0
			nchargesvat=0
			ncharges_exvat=0
			for ride in rides:
				ntotal=ntotal + ride.ritprijs + ride.wachttijd
				nchargesvat=nchargesvat+ride.charges_vat
				ncharges_exvat=ncharges_exvat+ride.charges_exvat
		 		ride.invoice_id=new_invoice
		 		ride.state='invoiced'
		 	if ntotal > 0:
		 		self._create_invoice_line(new_invoice, ntotal,ride.company_id.default_rides_product)
		 		if ride.partner_id.diesel > 0:
		 			self._create_invoice_line(new_invoice, ntotal * (ride.partner_id.diesel/100),ride.company_id.default_diesel_product)
		 	if nchargesvat > 0:
		 		self._create_invoice_line(new_invoice, nchargesvat,ride.company_id.default_charges_vat_product)

		 	if ncharges_exvat > 0:
		 		self._create_invoice_line(new_invoice, ncharges_exvat,ride.company_id.default_charges_exvat_product)
		 	new_invoice.button_reset_taxes()


		
		return invoices

	def _create_invoice_line(self,curr_invoice, nprice_unit,product):
		taxes = product.taxes_id or product.categ_id.property_account_income_categ.tax_ids
		tax = self.env['account.fiscal.position'].browse(curr_invoice.fiscal_position.id).map_tax(taxes)
		new_line={
		'invoice_id': curr_invoice.id,
		'price_unit': nprice_unit,
		'quantity': 1,
		'product_id': product.id,
		'uom_id': product.uom_id.id,
		'name': product.name,
		'account_id': product.property_account_income.id or product.categ_id.property_account_income_categ.id,
		'invoice_line_tax_id': tax
		}
		
		new_invoice_line=self.env['account.invoice.line'].create(new_line)
		

		new_invoice_line.invoice_line_tax_id=self.env['account.fiscal.position'].browse(curr_invoice.fiscal_position.id).map_tax(taxes)
		



class herstens_destination (models.Model):
	_name="hertsens.destination"
	_order="sequence"
	_rec_name = 'destination'

	
	destination=fields.Char()
	ref=fields.Char()
	remarks=fields.Char()
	rit_id=fields.Many2one('hertsens.rit')
	sequence=fields.Integer(required=True, default=100)
	place_id=fields.Many2one('res.partner', string="Location", ondelete='restrict')
	activity_id=fields.Selection([('load','Load'),('unload','Unload')] , required=True)
	vehicle_id=fields.Many2one('fleet.vehicle', copy=False)
	state=fields.Selection([('planned','Planned'),('dispatched','Dispatched'),('cancelled', 'Cancelled'),('completed','Completed'),('waiting','Waiting for info'),('toinvoice','To be invoiced'),('invoiced','Invoiced')], required=True, default='planned')

	def cancel_transics_planning(self):
		planningitemselection={'PlanningSelectionType':'PLACE',
								'ID':str(self.rit_id.id) + '_' + str(self.id)
								}
		response=self.env['transics.transics'].Cancel_Planning(planningitemselection)
		if response['Errors']:
			raise exceptions.Warning(response)
		else:
			self.state='cancelled'


class User(models.Model):
    _inherit = 'res.users'
    operational_mode=fields.Selection([('off','off'),('on','on')], default="off", string="Operational mode", help="If operational mode is on, customers and invoices of all the companies are shown. No accounting actions are possible.")


class invoice(models.Model):
	_inherit="account.invoice"
	rides_ids=fields.One2many( "hertsens.rit" ,"invoice_id")
	on=fields.Char(required=True,default="on")
	rides_csv_data=fields.Binary(readonly=True)
	rides_csv_save=fields.Char()

	@api.multi
	def action_cancel(self,vals=None,context=None):
		#pdb.set_trace()	
		# code om te vermijden dat uitgaande facturen worden geannuleerd als er al ritten aanhangen.
		# voor inkomende facturen verandert er niets.
		if self.type == 'in_invoice':
			return super(invoice, self.with_context(from_parent_object=True)).action_cancel()
		if self.state == 'draft':
			for ride in self.rides_ids:
				#self.env['hertsens.rit']
				ride.sudo().state='toinvoice'
				ride.sudo().invoice_id=""
				self.rides_csv_save=None
				self.rides_csv_data=None
			return super(invoice, self.with_context(from_parent_object=True)).action_cancel()
		else:
			raise exceptions.Warning(_("Annuleren onmogelijk in deze factuurstatus."))
			
	@api.multi
	def generate_csv_data(self, context=None):
		self.rides_csv_save="detail-%s.csv" % self.number
		self.rides_csv_save=self.rides_csv_save.replace("/","_")
		#self.rides_csv_file="details"
		#self.rides_csv_file=base64.encodestring(self.rides_csv_file.encode('utf8'))
		
		self.rides_csv_data="date,departure,destination,cmr,ref,price,charges_vat,charges_exvat,total\n"
		for ride in self.rides_ids:
			self.rides_csv_data += "%s," % ride.datum
			self.rides_csv_data += "%s," % ride.vertrek
			self.rides_csv_data += "%s," % ride.bestemming
			self.rides_csv_data += "%s," % ride.cmr
			self.rides_csv_data += "%s," % ride.refklant
			self.rides_csv_data += "%s," % ride.ritprijs
			self.rides_csv_data += "%s," % ride.charges_vat
			self.rides_csv_data += "%s," % ride.charges_exvat
			self.rides_csv_data += "%s," % ride.total_ride_price
			self.rides_csv_data += "\n" 
		self.rides_csv_data=base64.encodestring(self.rides_csv_data.encode('utf-8'))	
		#pdb.set_trace()


class invoice_line(models.Model):
	_inherit="account.invoice.line"
	on=fields.Char(required=True,default="on")

class account_move(models.Model):
	_inherit="account.move"
	on=fields.Char(required=True,default="on")

class bank_statement(models.Model):
	_inherit="account.bank.statement"
	on=fields.Char(required=True,default="on")






class res_company(models.Model):
	_inherit= "res.company"
	default_rides_product=fields.Many2one('product.product', string="Product rides", help="Product to use for rides")
	default_diesel_product=fields.Many2one('product.product', string="Product diesel surcharge",help="Product to use for diesel surcharge")
	default_charges_vat_product=fields.Many2one('product.product', string="Product charges vat",help="Product to use for charges including vat")
	default_charges_exvat_product=fields.Many2one('product.product', string="Product charges ex vat", help="Product to use for charges with vat exempt")


class hertsens_invoice_create(models.TransientModel):
	_name='hertsens.invoice.create'
	date=fields.Date(string="Invoice date",required=True, default=date.today())
	oneline=fields.Boolean(default=True,help="1 invoice line for all rides?")
	allrides_valid=fields.Boolean(default=False)
	def _default_rides(self):
		return self._context.get('active_ids')
	rides_ids=fields.Many2many('hertsens.rit', default=_default_rides)

	@api.onchange('rides_ids')
	def _check_validity(self):
		self.allrides_valid=True
		for ride in self.rides_ids:	
			if not ride.state == 'toinvoice':
				self.allrides_valid=False

	# @api.multi
	# def do_create(self):
	# 	invs = []
	# 	mod_obj = self.env['ir.model.data']
	# 	act_obj = self.env['ir.actions.act_window']
	# 	mod_ids = mod_obj.search([('name', '=', 'action_invoice_tree1')])
	# 	res_id = mod_obj.browse(mod_ids)
	# 	act_win = act_obj.browse(res_id)
	# 	pdb.set_trace()
	# 	act_win.domain = [('id','in',invs),('type','=','out_invoice')]
	# 	pdb.set_trace()
	# 	act_win['name'] = _('Invoices')
	# 	pdb.set_trace()
	# 	return act_win
	def do_create(self, cr, uid, ids, context=None):
		data = self.read(cr, uid, ids, context=context)[0]
		# Create an invoice based on selected timesheet lines
		invs = self.pool.get('hertsens.rit').invoice_cost_create(cr, uid, context['active_ids'], data, context=context)
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		mod_ids = mod_obj.search(cr, uid, [('name', '=', 'action_invoice_tree1')], context=context)
		res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)[0]['res_id']
		act_win = act_obj.read(cr, uid, [res_id], context=context)[0]
		act_win['domain'] = [('id','in',invs),('type','=','out_invoice')]
#		act_win['domain'] = [('type','=','out_invoice')]
		act_win['name'] = _('Invoices')
		return act_win

class hertsens_dow(models.Model):
	_name="hertsens.dow"
	_description="Day of week"
	name=fields.Char(String="Full day name")
	day_number=fields.Integer()
