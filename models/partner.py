# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import date

class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    instructor = fields.Boolean("Instructor", default=False)

    session_ids = fields.Many2many('openacademy.session',
                                   string="Attended Sessions", readonly=True)



    def btn_fact(self):
        lines = []
        for session in self.session_ids:

            line ={
                'name': session.name,
                'quantity': session.duration,
                'price_unit': session.pu
            }

            lines.append(line)

        # counts = len(lines)

        invoice = self.env['account.move'].create({
            'type': 'out_invoice',
            'partner_id': self.id,
            'invoice_date': date.today(),
            'date': date.today(),
            'invoice_line_ids': [(0, 0, line) for line in lines]
            })