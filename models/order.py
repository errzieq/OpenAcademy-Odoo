from odoo import fields, models
from datetime import date
import pandas as pd
from pprint import pprint

class order(models.Model):
    _inherit = 'sale.order'

    def action_create_facture(self):
        # if self.filtered(lambda so: so.state != 'draft'):
        #     raise UserError(_('Only draft orders can be marked as sent directly.'))
        # for order in self:
        #     order.message_subscribe(partner_ids=order.partner_id.ids)
        # self.write({'state': 'sent'})
        # for self.filtered(lambda so: so.partner_id != 'draft'):
        #

        #peut grouper ici order_line des costumers et supprimer filtrage lambda (demain)

        for i in self.partner_id: #self is here sale.order
            pprint(self.id) #self.partner_id = res.partner(2,) et self.env.uid = 2 or self.partner_id.id = 2
            lines = []
            for session in self.order_line.filtered(lambda x: x.order_id.partner_id.id == i.id): #x is like order_line
                pprint(session.order_id)
                line = {
                    'name': session.name,
                    'quantity': session.product_uom_qty,
                    'price_unit': session.price_unit,
                }
                lines.append(line)
            # .read_group(domain, ['balance', 'account_id']
            # self.env['sale.order.line'].read_group([], fields=['name', 'product_uom_qty', 'price_unit'],
            #                                        groupby=['name', 'product_uom_qty'], lazy=False)

            df = pd.DataFrame(lines)
            pprint(df)
            g = df.groupby(['name', 'price_unit'], as_index=False)['quantity'].sum()
            pprint(g)
            lines = g.to_dict('r')
            #
            # pprint(lines)

            # counts = len(lines)
            invoice = self.env['account.move'].create({
                'type': 'out_invoice',
                'partner_id': i,
                'invoice_date': date.today(),
                'date': date.today(),
                'invoice_line_ids': [(0, 0, line) for line in lines]
            })
