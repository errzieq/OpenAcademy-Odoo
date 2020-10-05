# -*- coding: utf-8 -*-
{
    'name': "openacademy",

    'summary': """Manage trainings""",

    'description': """
        Open Academy module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'board', 'mail','account','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/openacademy.xml',
        'security/security.xml',
        'views/partner.xml',
        'views/session_board.xml',
        'reports.xml',
        'views/mycourses.xml',
        'views/reports_contact.xml',
        'views/invoices.xml',
        'views/report_invoice.xml',
        'views/action_order.xml',
        # 'views/portal.xml',
        'views/session_templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
}
