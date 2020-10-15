# -*- coding: utf-8 -*-
import binascii
from datetime import date

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from pprint import pprint
from datetime import timedelta, date
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.http import local_redirect
from odoo.osv.expression import AND

# class Openacademy(http.Controller):
#     @http.route('/openacademy/openacademy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/openacademy/openacademy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('openacademy.listing', {
#             'root': '/openacademy/openacademy',
#             'objects': http.request.env['openacademy.openacademy'].search([]),
#         })

#     @http.route('/openacademy/openacademy/objects/<model("openacademy.openacademy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('openacademy.object', {
#             'object': obj
#         })

class sessionPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(sessionPortal, self)._prepare_portal_layout_values()
        return values

    def _prepare_home_portal_values(self):
        values = super(sessionPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id

        # SaleOrder = request.env['sale.order']
        ResPartner = request.env['res.partner']
        # quotation_count = SaleOrder.search_count([
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sent', 'cancel'])
        # ])

        # order_count = SaleOrder.search_count([
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sale', 'done'])
        # ])
        # pprint(request.env['res.partner'].user_id.id)
        # pprint(request.env.user.partner_id.id)
        # pprint()
        # domain = [('3', '=', request.env.user.partner_id.id)]
        session_count = len(request.env.user.partner_id.session_ids)
        pprint(request.env.user.partner_id.session_ids)

        # i = 0
        # if request.env.user.partner_id.id == 3: # 3 = request.env['res.partner'].partner_id.id
        #     session_count = i = i+1
        # values.update({
        #     'quotation_count': quotation_count,
        #     'order_count': order_count,
        # })

        values.update({
            'session_count': session_count
        })
        return values

    # Quotations and Sales Orders
    #
    @http.route(['/my/session', '/my/session/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_session(self, page=1, date_begin=None, date_end=None, sortby=None,search=None, search_in='name', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        name = request.env.user.partner_id.session_ids
        pprint(partner.id)
        ResPartner = request.env['res.partner']

        domain = ['|',('instructor_id','=',request.env.user.partner_id.id),('attendee_ids','in',request.env.user.partner_id.id)]

        # domain = [
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sent', 'cancel'])
        # ]

        # searchbar_sortings = {
        #     'date': {'label': _('Order Date'), 'order': 'date_order desc'},
        #     'name': {'label': _('Reference'), 'order': 'name'},
        #     'stage': {'label': _('Stage'), 'order': 'state'},
        # }

        searchbar_sortings = {
            'name': {'label': _('name session'), 'order': 'name'} #request.env.user.partner_id.session_ids
        }

        

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search by name')},
        }

        # default sortby order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # archive_groups = self._get_archive_groups('res.partner', domain) if values.get('my_details') else []
        # if date_begin and date_end:
        #     domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        if search and search_in:
            domain.insert(0, ('name', 'ilike', search))


        print(domain)

        # count for pager
        # quotation_count = SaleOrder.search_count(domain)
        session_count = len(request.env.user.partner_id.session_ids.search(domain))
        pprint(request.env['openacademy.session'].search(domain))

        # make pager
        pager = portal_pager(
            url="/my/session",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=session_count,
            page=page,
            step=self._items_per_page,
        )


        # search the count to display, according to the pager data
        sessions = request.env.user.partner_id.session_ids.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        # pprint(sessions)
        # sessions = sessions.search([])
        request.session['my_session_history'] = sessions.ids[:100]
        pprint(sessions.sudo())
        values.update({
            'date': date_begin,
            'sessions': sessions.sudo(),
            'page_name': 'session',
            'pager': pager,
            'search_in': search_in,
            # 'archive_groups': archive_groups,
            'default_url': '/my/session',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs
        })
        # return request.render("sale.portal_my_quotations", values)
        return request.render("openacademy.portal_my_home_menu_contact_sessions2", values)


    @http.route(['/my/session/<int:session_id>'], type='http', auth="public", website=True)
    def portal_session_page(self, session_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            session_sudo = self._document_check_access('openacademy.session', session_id, access_token=access_token) #print
        except (AccessError, MissingError):
            return request.redirect('/my')
        partner_id = request.env.user.partner_id.id
        session_sudo1 = self._document_check_access('openacademy.session', session_id, access_token=access_token) #download
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=session_sudo1, report_type=report_type,
                                     report_ref='openacademy.report_session', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        pprint(session_sudo)
        if session_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_quote_%s' % session_sudo.id)
            if isinstance(session_obj_date, date):
                session_obj_date = session_obj_date.isoformat()
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_quote_%s' % session_sudo.id] = now
                body = _('Quotation viewed by customer %s') % session_sudo.partner_id.name
                _message_post_helper(
                    "openacademy.session",
                    session_sudo.id,
                    body,
                    token=session_sudo.access_token,
                    message_type="notification",
                    subtype="mail.mt_note",
                    partner_ids=session_sudo.instructor_id.id,
                )
        pprint(session_sudo.instructor_id.id)
        values = {
            'openacademy_session': session_sudo,
            'res_partner': session_sudo.instructor_id,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': request.env.user.partner_id.id,
            'report_type': 'html',
            'session_id': session_id
            # 'action': session_sudo._get_portal_return_action(),
        }
        # if order_sudo.company_id:
        #     values['res_company'] = order_sudo.company_id

        # if order_sudo.has_to_be_paid():
        #     domain = expression.AND([
        #         ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
        #         ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
        #     ])
        #     acquirers = request.env['payment.acquirer'].sudo().search(domain)
        #
        #     values['acquirers'] = acquirers.filtered(
        #         lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
        #                     (acq.payment_flow == 's2s' and acq.registration_view_template_id))
        #     values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total,
        #                                                                  order_sudo.currency_id,
        #                                                                  order_sudo.partner_id.country_id.id)
        #
        # if order_sudo.state in ('draft', 'sent', 'cancel'):
        #     history = request.session.get('my_quotations_history', [])
        # else:
        #     history = request.session.get('my_orders_history', [])
        # values.update(get_records_pager(history, order_sudo))

        return request.render('openacademy.res_partner_portal_template', values)

# class WebsiteForm(WebsiteForm):

    @http.route("/my/session/create", type='http', auth="public", website=True)
    def create_session(self, **kwargs):
        # user = request.env['res.partner'].sudo().search([('id', '=', request.env.user.partner_id.id)])
        users = request.env['res.partner'].sudo().search(['|', ('instructor', '=', True),
                                                          ('category_id.name', 'ilike', "Teacher")])



        default_values = {
            'start_date': date.today(),
            # 'instructor': user.name,
            'users': users
        }

        users = request.env['res.partner'].sudo().search([])
        pprint(users.ids)
        return request.render("openacademy.session_submit", default_values)

    @http.route('/website_form_create', type='http', auth="public", methods=['POST'], website=True)
    def website_form_create(self, access_token=None, **kwargs):
        users = request.env['res.partner'].sudo().search([('name', '=', kwargs['instructor'])])

        pprint(users)
        session = request.env['openacademy.session'].create({
            'name': kwargs['name'],
            'start_date': kwargs['start_date'],
            'pu': kwargs['pu'],
            'duration': kwargs['duration'],
            'instructor_id': users.id
        })

        pprint(session)
        return local_redirect("/my/session/%d" % session.id)
        # return super(WebsiteForm, self).website_form(model_name, **kwargs)

    @http.route("/my/session/update/<int:session_id>", type='http', auth="public", website=True)
    def update_session(self, session_id, report_type=None, access_token=None, message=False, download=False, **kwargs):
        try:
            session_sudo = session_id
        except (AccessError, MissingError):
            return request.redirect('/my')
        print(session_id)

        id = request.env.user.partner_id.id
        user = request.env['res.partner'].sudo().search([('id', '=', id)])
        session = request.env['openacademy.session'].sudo().search([('id', '=', session_id)])
        users = request.env['res.partner'].sudo().search(['|', ('instructor', '=', True),
                                                          ('category_id.name', 'ilike', "Teacher")])
        users_name = []
        for i in users:
            users_name.append(i.name)

        valuess = {
            'session_id': session_id,
            'start_date': date.today(),
            'instructor': request.env.user.partner_id.id,
            'user': user,
            'session': session,
            'users': users_name
        }
        pprint(valuess['user'].name)
        pprint(valuess['session'].name)

        return request.render("openacademy.session_update", valuess)

    @http.route(['/website_form_update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, access_token=None, **kwargs):
        employee = request.env['openacademy.session'].search([('id', '=', kwargs['x'])])
        users = request.env['res.partner'].sudo().search([('name', '=', kwargs['instructor'])])
        pprint(users)
        employee.write({
            'name': kwargs['name'],
            'start_date': kwargs['start_date'],
            'pu': kwargs['pu'],
            'duration': kwargs['duration'],
            'instructor_id': users.id
        })
        print(employee.name)
        return local_redirect("/my/session")
        # return request.render("openacademy.session_submited", {})
        # return super(WebsiteForm, self).website_form(model_name, **kwargs)

    @http.route(['/delete_session'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, access_token=None, **kwargs):
        record_delete = request.env['openacademy.session'].search([('id', '=', kwargs['id'])])
        print(record_delete)
        record_delete.unlink()

        return local_redirect("/my/session")
