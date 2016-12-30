from openerp import models, fields, api, exceptions, _
from openerp.http import request
from openerp.exceptions import ValidationError

from openerp.osv import fields, osv



class hertsens_config_settings(osv.osv_memory):
    _name = 'hertsens.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
    'follower_id': fields.many2one('res.users', 'Follower'),
    'message_template_id': fields.many2one('esms.templates', 'Template'),
    'follower_value':fields.integer('Follower int id'),
    }

    def create(self, cr, uid, values, context=None):
        id = super(hertsens_config_settings, self).create(cr, uid, values, context)
        # Hack: to avoid some nasty bug, related fields are not written upon record creation.
        # Hence we write on those fields here.
        vals = {}
        for fname, field in self._columns.iteritems():
            if isinstance(field, fields.related) and fname in values:
                vals[fname] = values[fname]
        self.write(cr, uid, [id], vals, context)
        return id










# class zzzhertsens_config_settings(models.TransientModel):
#     _name = 'zzzhertsens_base.config.settings'
#     _inherit = 'res.config.settings'

#     # def _get_default_reveal_credentials_timeout(self):
#     #     return self.env['ir.config_parameter'].get_param('hertsens_base.reveal_credentials_timeout', '') or 15000

#     #reveal_credentials_timeout = fields.Integer('Reveal Credentials Timeout (ms)', required=True, default=_get_default_reveal_credentials_timeout)
#     message_template=fields.Many2one("esms.templates")
#     follower=fields.Many2one("res.users")
#     # @api.model
#     # def set_reveal_credentials_timeout(self, ids):
#     #     config = self.browse(ids[0])
#     #     icp = self.env['ir.config_parameter']
#     #     icp.set_param('hertsens_base.reveal_credentials_timeout', config.reveal_credentials_timeout)
    
#     def create(self, cr, uid, values, context=None):
#         id = super(hertsens_config_settings, self).create(cr, uid, values, context)
#         # Hack: to avoid some nasty bug, related fields are not written upon record creation.
#         # Hence we write on those fields here.
#         vals = {}
#         for fname, field in self._columns.iteritems():
#             if isinstance(field, fields.related) and fname in values:
#                 vals[fname] = values[fname]
#         self.write(cr, uid, [id], vals, context)
#         return id