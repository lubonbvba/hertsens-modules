# -*- coding: utf-8 -*-
{
    'name': "hertsens_planning",

    'summary': """
        Modifications to odoo project for hertsens planning""",

    'description': """
        This module extends the standard odoo project functionality for the planning of vans and trucks
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hertsens',
    'version': '0.24',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hertsens_base', 'project', 'fleet','hr', 'entity_sms'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
#        'data/project_data.xml',
        'data/vehicle_data.xml',
#        'data/migrate.xml',
#        'views/fleet_modif.xml',
#        'views/project_modif.xml',
#        'views/hertsens_base_modif.xml',
#        'views/planning.xml',
#        'views/users_modif.xml',
 #       'views/hr_modif.xml',
    ],
    'sequence': '500',
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}