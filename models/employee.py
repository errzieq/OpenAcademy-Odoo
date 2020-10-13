# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import date

class Partner(models.Model):
    _inherit = 'hr.employee'

    marital = fields.Selection([
        ('Single with children', 'Single with children'),
        ('Single without children', 'Single without children'),
        ('Married with children', 'Married with children'),
        ('Married without children', 'Married without children'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="hr.group_hr_user", default='single', tracking=True)