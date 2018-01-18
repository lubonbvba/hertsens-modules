# -*- coding: utf-8 -*-

from openerp import models, fields, api
import pdb
import openerp
import logging

class EsmsHistory(models.Model):

    _inherit = "esms.history"



    @api.model
    def create(self, values):
        new_rec = super(EsmsHistory, self).create(values)
        if not new_rec.service_message:
            last_ride=self.env["hertsens.rit"].search([('last_msg','=',new_rec.from_mobile)])
            if last_ride:
                last_ride.message_post(body=new_rec.sms_content,
                     subject="Rit: " + str(last_ride.id) + "," + last_ride.display_name + " van: " + (new_rec.partner_id.name or new_rec.from_mobile),
                     type = 'comment',
                     subtype = "mail.mt_comment")
            elif new_rec.direction == 'I':
                #pdb.set_trace()
                self.env['res.users'].browse(62).message_post(body=new_rec.sms_content,
                     subject="Niet toe te wijzen sms van: " + (new_rec.partner_id.name or new_rec.from_mobile),
                     type = 'comment',
                     subtype = "mail.mt_comment")

        return new_rec





class esms_compose(models.Model):

    _inherit = "esms.compose"


    @api.multi
    def send_entity(self):
    	new_rec = super(esms_compose, self).send_entity()
        #pdb.set_trace()
        if self.model_id == 'hertsens.rit':
            self.env[self.model_id].browse(self.record_id).set_last_msg(self.to_number,self.sms_content)

        return new_rec


