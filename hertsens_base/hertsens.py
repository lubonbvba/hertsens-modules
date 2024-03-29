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
	invoice_id=fields.Many2one('account.invoice', ztrack_visibility='onchange')
	destination_ids=fields.One2many('hertsens.destination','rit_id')
	finished=fields.Boolean(help="Tick if ride is finished")
	state=fields.Selection([('quoted','Quote'),('planned','Planned'),('predispatched','Pre Dispatched'),('dispatched','Dispatched'),('cancelled', 'Cancelled'),('completed','Completed'),('waiting','Waiting for info'),('toinvoice','To be invoiced'),('invoiced','Invoiced')], required=True, default='planned', ztrack_visibility='onchange')
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
	hist_ids=fields.One2many('hertsens.destination.hist','ride_id')
	driver_id=fields.Many2one('hr.employee')
	default_vehicle_id=fields.Many2one('fleet.vehicle', string="Voorzien voertuig", help="Voertuig voorzien voor deze rit")
	time_load=fields.Char(string="Gevraagde laadtijd",  help="Informatief veld, hier gebeurt verder niets mee" )
	time_unload=fields.Char(string="Gevraagde lostijd", help="Informatief veld, hier gebeurt verder niets mee" )
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
	@api.onchange('default_vehicle_id')
	def _checkstate_based_on_default_vehicle(self):
		if self.default_vehicle_id:
			self.state='predispatched'
		else:
			self.state='planned'


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
		if self.state not in ['cancelled','invoiced']:
		# do not change state if ride is cancelled, invoiced
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
		try:
			if nr_dest>=2:
				if destinations[0].place_id:
					self.google_navigation_url+="&origin="+ destinations[0].place_id.get_geoXY_string()[0]
				if destinations[nr_dest-1].place_id:	
					self.google_navigation_url+="&destination="+ destinations[nr_dest-1].place_id.get_geoXY_string()[0]
				if nr_dest>2:
					self.google_navigation_url+="&waypoints="
					nvia=0
					for via in range(1,nr_dest-1):
						if destinations[via].place_id:
							self.google_navigation_url+= destinations[via].place_id.get_geoXY_string()[0] + "|"
		except:
			pdb.set_trace()
			#raise exceptions.Warning("Probleem met lege bestemming, id: %d", self.id )			

	@api.multi
	def check_rit_status(self):
		if len(self)==1:
			if self.state not in ['invoiced','toinvoice']:
				for hist in self.hist_ids:
					if hist.cmr:
						#cmr exists in hist
						if not self.cmr:
							#no cmr exixte yet
							self.cmr=hist.cmr
						elif self.cmr.find(hist.cmr) == -1:
							#cmr exists end hist.crm not founf in cmr
							self.cmr += ","
							self.cmr+=hist.cmr				
				for dest in self.destination_ids:
					if dest.employee_id:
						self.driver_id=dest.employee_id
#				if self.destination_ids.search(['&',('rit_id',"=",self.id),('state','in',['planned','cancelled', 'aborted'])]):
				if self.destination_ids.search(['&',('rit_id',"=",self.id),('state','in',['planned'])]):
					self.state='planned'
					return
				if self.destination_ids.search(['&',('rit_id',"=",self.id),('state','in',['received','read','progress'])]):
					self.state='dispatched'
					return
				if self.destination_ids.search(['&',('rit_id',"=",self.id),('state','in',['completed'])]):
					#self.state='completed'
					#self.cmr=""

					self.finished=True
					self._checkstate()
					return
	@api.multi
	def refresh_ride(self):
		#functie om statussen na te kijken bij gereden ritten en evt cmr info up te daten.
		#via meer menu
		for rit in self:
			if rit.finished:
				new_cmr=""
				for hist in rit.hist_ids:
					if new_cmr and hist.cmr:
						new_cmr += ","
					if hist.cmr:
						new_cmr+=hist.cmr
				if new_cmr:
					rit.cmr=new_cmr
				rit._checkstate()			

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
				for destination in ride.destination_ids.sorted(key=lambda l: l.sequence):
					newdest=destination.copy({
						'rit_id':new.id,
						'vehicle_id':None,
						'datum':new.datum,
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
			'name': data['ref'] or "%s - %s" % (time.strftime('%d/%m/%Y'), ride.partner_id.name),
        	'partner_id': ride.partner_id.id,
        	'company_id': ride.company_id.id,
        	'payment_term': ride.partner_id.property_payment_term.id or False,
		'payment_mode_id': ride.partner_id.customer_payment_mode.id, 
        	'date_invoice': data['date'],
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
	
	@api.multi
	def refresh_transics(self):
		self.env['transics.transics'].dispatcher_query()


	@api.multi	
	def dispatch_transics_wizard(self):
#		pdb.set_trace()
		wiz=self.env['planning.transics.wizard'].create({
#			'ride_ids': [(6, None, [self.id])],
#			'name': self.name_get(),
#			'vehicle_type_id': self.vehicle_type_id.id,
			'vehicle_id':self.default_vehicle_id.id,
			})
		#for ride in self:
		res=wiz._get_destinations(self)
		action = {
                'name': 'Dispatch Transics Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'planning.transics.wizard',
                'domain': [],
                'context': self.env.context,
                'res_id': wiz.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
   		#pdb.set_trace()
   		return action
	@api.one
	def _get_valid_activity_ids(self):
		self.valid_activity_ids=self.env['transics.activity'].search([('transics_account_id', '=', self.env.user.company_id.transics_account_id.id),('dispatch_enabled','!=',False)])

	valid_activity_ids=fields.Many2many("transics.activity", compute="_get_valid_activity_ids")



class herstens_destination (models.Model):
	_name="hertsens.destination"
	_order="rit_id,sequence,id"
	_rec_name = 'destination'

	
	destination=fields.Char()
	ref=fields.Char()
	remarks=fields.Char()
	rit_id=fields.Many2one('hertsens.rit', ondelete='cascade')
	sequence=fields.Integer(required=True, default=10)
	place_id=fields.Many2one('res.partner', string="Location", ondelete='restrict', required=True)
	activity_id=fields.Selection([('load','Load'),('unload','Unload')] , zrequired=True, readonly=True)
	transics_activity_id=fields.Many2one('transics.activity', string="Act" ,required=True, domain="[('id','in',valid_activity_ids[0][2])]", ondelete='restrict')
	vehicle_id=fields.Many2one('fleet.vehicle', copy=False)
	employee_id=fields.Many2one('hr.employee', string="Driver", copy=False)
	datum=fields.Date(help="Datum dat deze operatie uitgevoerd moet worden, informatief veld")
	state=fields.Selection([('planned','Planned'),('dispatched','Dispatched'),('received', 'Received'),('read', 'Read'),('cancelled', 'Cancelled'),('aborted', 'Aborted'),('progress','In progress'),('completed','Completed')], required=True, default='planned')
	hist_ids=fields.One2many('hertsens.destination.hist','hertsens_destination_id')

	valid_activity_ids=fields.Many2many("transics.activity", related='rit_id.valid_activity_ids')



	@api.multi
	def cancel_transics_planning(self):
		for place in self.hist_ids:
			if (place.status == "NOT_EXECUTED" or place.lastupdate == False) and self.state in ['dispatched','received','read']:
				place.cancel_transics_planning()
				self.status='cancelled'
				place.cancelstatus='cancel_sent'
	@api.one			
	def _caclculate_sequence(self):
		self.sequence_calc=self.sequence
		return self.sequence			
	sequence_calc=fields.Integer(string="Seq", compute=_caclculate_sequence)

	@api.multi
	def check_dest_status(self):
		if len(self.hist_ids)>0:
			hist=self.hist_ids[-1]
			if hist.status=='CANCELED':
				self.state='cancelled'
			if hist.status=='ABORTED':
				self.state='aborted'	
			if hist.transferstatus == 'READ_PLANNING':
				self.state='read'
			if hist.status=='NOT_EXECUTED' and hist.transferstatus=='DELIVERED':
				self.state='received'
			if hist.status=='BUSY':
				self.state='progress'
			if hist.status=='FINISHED':
				self.state='completed'
			self.employee_id=hist.employee_id
			if self.rit_id:
				self.rit_id.check_rit_status()
			else:
				_logger.warning("Destination without ride, last hist: %s" % hist.place_id)
		

		


class herstens_destination_hist (models.Model):
	_name="hertsens.destination.hist"
	_sql_constraints = {
		('place_id_uniq', 'unique(place_id)', 'Place ID not unique, contact Lubon')
	}
	hertsens_destination_id=fields.Many2one('hertsens.destination' , ondelete='restrict')
	ride_id=fields.Many2one('hertsens.rit', ondelete='restrict')
	state=fields.Selection([('sent','Sent'),('cancelled','Cancelled')])
	place_id=fields.Char()
	vehicle_id=fields.Many2one('fleet.vehicle')
	ref=fields.Char()
	remarks=fields.Char()
	cancelstatus=fields.Char()
	status=fields.Char()
	transferstatus=fields.Char()
	lastupdate=fields.Datetime()
	employee_id=fields.Many2one('hr.employee', string="Driver")
	raw=fields.Char()
	cmr=fields.Char()
	pallet_load=fields.Integer()
	pallet_unload=fields.Integer()
	longitude=fields.Float()
	latitude=fields.Float()
	km=fields.Integer()
	arrivaldate=fields.Datetime()
	leavingdate=fields.Datetime()
	geo_lookupname=fields.Char()
	transics_activity_id=fields.Many2one('transics.activity', related='hertsens_destination_id.transics_activity_id')
	activity_id=fields.Selection( related='hertsens_destination_id.activity_id')

	@api.multi
	def create_transics_planning(self, destination_id, vehicle_id,ref,remarks,wiz_id):
		hist=self.env['hertsens.destination.hist'].create({
			'hertsens_destination_id':destination_id.id,
			'vehicle_id':vehicle_id.id,
			'ref':ref,
			'remarks':remarks,
			'ride_id': destination_id.rit_id.id,
			})
		hist.place_id=self.env.cr.dbname + '_' + str(wiz_id) + '_' + str(hist.id)
		places=[]
		nseq=10
		planninginsert= {'Vehicle':{'IdentifierVehicleType':'ID','Id':vehicle_id.vehicle_transics_id }}
		placesinsert={
			'OrderSeq':hist.id,
			'PlaceId':hist.place_id,
			'DriverDisplay': ('ID:' + ' ' + str(hist.ride_id.id ) + ',('+ hist.hertsens_destination_id.place_id.country_id.code + ') ' + (hist.hertsens_destination_id.place_id.geo_name or "Onbekend"))[:50],
			'Comment':  hist.hertsens_destination_id.place_id.name + ", " + (hist.hertsens_destination_id.place_id.geo_name or "Onbekend"),  
#				'ExecutionDate': '2017-12-04T18:00:00',
			'Activity':{},
#				'AlarmTimeETA':'True',
#				'CustomNr':'True',
			'Position':{'Longitude':hist.hertsens_destination_id.place_id.geo_longitude,'Latitude':hist.hertsens_destination_id.place_id.geo_latitude},
#				'SalesPrice':'True'
		}
		#Set activity field
#		if hist.hertsens_destination_id.activity_id == 'load':
#			placesinsert['Activity']['ID']=self.env['ir.config_parameter'].get_param('transics.act_load_id', '')
#		if hist.hertsens_destination_id.activity_id == 'unload':
#			placesinsert['Activity']['ID']=self.env['ir.config_parameter'].get_param('transics.act_unload_id', '')
		placesinsert['Activity']['ID']=hist.hertsens_destination_id.transics_activity_id.transics_id
		#pdb.set_trace()

		#Complet Comment field	
		if ref:	
			placesinsert['Comment']	+= '\nRef: ' + ref
		if remarks:	
			placesinsert['Comment']	+= '\n' +	remarks
		if True:
			placesinsert['Comment']	+= '\n\nDebug info:' +	hist.place_id
		nseq+=10
		places.append(placesinsert)
		planninginsert['Places']={'PlaceInsert':places}
#		response=self.env['transics.transics'].Insert_Planning(planninginsert)
		response=self.env.user.company_id.transics_account_id.Insert_Planning(planninginsert)
		if response['Errors']:
			raise exceptions.Warning(response)
		else:
			hist.state='sent'
			hist.hertsens_destination_id.state='dispatched'
			hist.hertsens_destination_id.vehicle_id=vehicle_id
	
	@api.multi				
	def cancel_transics_planning(self):	
		planningitemselection={'PlanningSelectionType':'PLACE',
								'ID':self.place_id
								}
#		response=self.env['transics.transics'].Cancel_Planning(planningitemselection)
		response=self.env.user.company_id.transics_account_id.Cancel_Planning(planningitemselection)
		if response['Errors']:
			raise exceptions.Warning(response)
		else:
			self.state='cancelled'
			if self.hertsens_destination_id:
				self.hertsens_destination_id.state='cancelled'
		#self.env['transics.transics'].dispatcher_query()


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
			self.rides_csv_data += "\"%s\"," % ride.datum
			self.rides_csv_data += "\"%s\"," % unicode(ride.vertrek).encode('ascii','ignore')
			self.rides_csv_data += "\"%s\"," % unicode(ride.bestemming).encode('ascii','ignore')
			self.rides_csv_data += '\"%s\",' % unicode(ride.cmr).encode('ascii','ignore')
			self.rides_csv_data += "\"\'%s\"," % unicode(ride.refklant).encode('ascii','ignore')
			self.rides_csv_data += "\"%s\"," % ride.ritprijs
			self.rides_csv_data += "\"%s\"," % ride.charges_vat
			self.rides_csv_data += "\"%s\"," % ride.charges_exvat
			self.rides_csv_data += "\"%s\"," % ride.total_ride_price
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
	oneline=fields.Boolean(default=False,help="1 invoice line for all rides?")
	allrides_valid=fields.Boolean(default=False)
	ref=fields.Char()	
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
