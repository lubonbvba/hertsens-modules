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
            mobile_e164=calc_e164(self.to_number)
            last_ride=self.env[self.model_id].search([('last_msg','=',mobile_e164)])
            for rit in last_ride:
                rit.last_msg=""
            rit=self.env[self.model_id].browse(self.record_id)
            rit.last_msg=mobile_e164
            rit.message_post(body=self.sms_content,
                 subject="Rit: " + str(rit.id) + "," + rit.display_name + " Drv: " + rit.driver_id.name,
                 type = 'comment',
                 #subtype = "mail.mt_comment"
                 )
            rit.message_subscribe_users(user_ids=62)
        return new_rec


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

