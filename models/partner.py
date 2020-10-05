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

    type_name = fields.Char('Type Name', default="Contact")

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (self.type_name, self.name)

    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """
            Get a portal url for this model, including access_token.
            The associated route must handle the flags for them to have any effect.
            - suffix: string to append to the url, before the query string
            - report_type: report_type query string, often one of: html, pdf, text
            - download: set the download query string to true
            - query_string: additional query string
            - anchor: string to append after the anchor #
        """
        self.ensure_one()
        url = '%s?access_token=%s%s%s' % (
            suffix if suffix else '',
            # self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            # '#%s' % anchor if anchor else ''
        )
        return url

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