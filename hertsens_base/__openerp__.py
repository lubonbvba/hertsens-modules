# -*- coding: utf-8 -*-
{
    'name': "hertsens_base",

    'summary': """
        Base modifications for Hertsens
        """,

    'description': """
        Modules will change stylesheets and change the invoice layout
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hertsens',
    'version': '0.43',

    # any module necessary for this one to work correctly
    'depends': ['base','account', 'entity_sms', 'base_iso3166', 'transics', 'project', 'fleet','hr'],

    # always loaded
    'data': [
    'security/security.xml',
    'security/hertsens_account_security.xml',
    'security/ir.model.access.csv',
#	'static/src/js/lubon_base.js',
#	'static/src/css/lubon_base.css',
    'templates.xml',
    'data/hertsens_cron.xml',
    'data/hertsens_dow.xml',
    'data/project_data.xml',
	'views/hertsens_base.xml',
	'views/hertsens_partners.xml',
    'views/hertsens_menu.xml',
    'views/hertsens_users.xml',
    'views/hertsens_account.xml',
    'views/hertsens_settings.xml',
    'views/hr_modif.xml',
#   'views/project_modif.xml',
    'views/fleet_modif.xml',
#    'views/hertsens_base_modif.xml',
    'views/planning_transics.xml',
#    'views/planning.xml',
    'views/users_modif.xml',
    'views/destinations.xml',
    'reports/hertsens_base_invoice.xml',
    'reports/hertsens_base_header.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
