# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import timedelta, date
from pprint import pprint

class Course(models.Model):
    _name = 'openacademy.course'
    _inherit = ['mail.thread','mail.activity.mixin'] #for chatter
    _description = "OpenAcademy Courses"

    name = fields.Char(string="Title", required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null', string="Responsible", index=True)

    # session_ids = fields.One2many('openacademy.session', 'course_id', string="Sessions")

    session_ids = fields.Many2many('openacademy.session', string="Sessions")

    # courses_ids = fields.Many2one('openacademy.department',
    #                             ondelete='cascade', string="Courses") #required=True

    department_id = fields.Many2one('openacademy.department', string="Department", required=True)

    #The object self.env gives access to request parameters and other useful things:
    # self.env.uid will return Id of Current Login User
    # self.env.user will return Current User Record
    # self.env[model_name] returns an instance of the given model
    # self.env.ref(xml_id) returns the record corresponding to an XML id

    chef_id = fields.Integer(string="Chef Department", compute='chef', store=True)
    

    @api.depends('department_id')
    def chef(self):
        for r in self:
            pprint('.........')
            users = self.env['openacademy.department'].sudo().search([('id', '=', r.department_id.id)])
            r.chef_id = users.chef_id.id
            pprint(r.chef_id)



    def _default_courses(self):
        #self : current login user
        #my_courses : give all courses
        my_courses = self.env['openacademy.course'].search_count([])
        values['my_courses'] = my_courses

    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            #self : current record
            [('name', '=like', _(u"Copy of {}%").format(self.name))])
        if not copied_count:
            new_name = _(u"Copy of {}").format(self.name)
        else:
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]

class Department(models.Model):
    _name = 'openacademy.department'
    _description = "OpenAcademy Department"

    name = fields.Char(required=True)
    chef_id = fields.Many2one('res.partner', string="Chef Department")
    # courses_ids = fields.One2many('openacademy.course', 'courses_ids', string="Courses", required=True)
    # sessions_ids = fields.One2many('openacademy.session', 'sessions_ids', string="Department", required=True)
    courses_ids = fields.One2many('openacademy.course', 'department_id',string="Courses") #required=True
    sessions_ids = fields.Many2many('openacademy.session', string="Sessions", required=True)

    def btn_ord(self):
        #self : current record

        lines = []
        for session in self.sessions_ids:

            line ={
                'product_id': session.id,
                'name': session.name,
                'product_uom_qty': session.duration,
                'price_unit': session.pu,
            }

            lines.append(line)
        #lines : liste des json
        # counts = len(lines)

        sale = self.env['sale.order'].create({
            'partner_id': self.id,
            'date_order': date.today(),
            'order_line': [(0, 0, line) for line in lines]
            })

class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date', inverse='_set_end_date')
    attendees_count = fields.Integer(string="Attendees count", compute='_get_attendees_count', store=True)
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()

    pu = fields.Float(digits=(6, 2), help="Prix Unitaire")

    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=['|', ('instructor', '=', True),
                                            ('category_id.name', 'ilike', "Teacher")]) #required=True

    # course_id = fields.Many2one('openacademy.course',
    #                             ondelete='cascade', string="Course", required=True)

    course_id = fields.Many2many('openacademy.course',
                                ondelete='cascade', string="Course", required=True, store=True)

    sessions_ids = fields.Many2one('openacademy.department',
                                 ondelete='cascade', string="Department", ) #required=True

    department_id = fields.Many2many('openacademy.department', string="Department", required=True)

    # chef_id = fields.Many2one('res.partner', string="Chef Department")

    # session have many attendees(res.partner) and attendee can participate in many sessions
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    course_count = fields.Integer(compute='compute_course_count', string="Number of Course")

    # smart button
    def course_list(self):
        action = self.env.ref('openacademy.course_list_action').read()[0]
        action['domain'] = [('id', 'in', self.course_id.ids)]
        action['views'] = [(self.env.ref('openacademy.course_tree_view').id, 'tree'),
                           (self.env.ref('openacademy.course_form_view').id, 'form')]
        action['context'] = {'default_responsible_id': self.id}
        return action

    @api.depends('course_id')
    def compute_course_count(self):
        for r in self:
            r.course_count = len(self.course_id)

    def get_portal_url(self):
        portal_link = "session/%s" % (self.id)
        return portal_link

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        for r in self:
            if r.seats < 0:
                return {
                    'warning': {
                        'title': _("Incorrect 'seats' value"),
                        'message': _("The number of available seats may not be negative"),
                    },
                }
            if r.seats < len(r.attendee_ids):
                return {
                    'warning': {
                        'title': _("Too many attendees"),
                        'message': _("Increase seats or remove excess attendees"),
                    },
                }

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(_("A session's instructor can't be an attendee"))

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

        # ----------------------------------------------------------------

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (self.name, self.env.user.name)

    def get_portal_urls(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
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

class Report(models.Model):
    _name = 'openacademy.report'
    _description = "OpenAcademy Report"
    _auto = False

    instru = fields.Many2one('res.partner', string="Instructor") #id many2one et remplacé id dans field de view... (voir pivot de session)
    session_name = fields.Char(readonly=True)
    courseid = fields.Many2many('openacademy.course', string="Course")
    course_name = fields.Char(readonly=True)
    sessionsid = fields.Many2many('openacademy.session', string="Session")
    responsible = fields.Char(readonly=True)
    #aussi resoudre probléme de session unique pour chaque cours

    def init(self):

        self._cr.execute("""
        CREATE OR REPLACE VIEW openacademy_report AS (
        Select row_number() over() as id, d.id as courseid, d.name as course_name, d.responsible_id as responsible,r.id as sessionsid , r.name as session_name, r.instructor_id as instru
        from openacademy_course as d
        join openacademy_course_openacademy_session_rel l
        on d.id = l.openacademy_course_id
        join openacademy_session as r
        on r.id = l.openacademy_session_id
        )""")
        # self._cr.execute("""
        # CREATE OR REPLACE VIEW openacademy_report2 AS (
        # Select e.name, e.responsible_id,v.chef_id, v.name as name_dep
        # from openacademy_course as e
        # inner join openacademy_department as v
        # on v.id = e.department_id
        # )""")

class Invoice(models.Model):
    _inherit = 'account.move'

    # Add a new column to the account.move model.
    # instructor = fields.Boolean("Instructor")
    # name= fields.Char("Instructor")
    # session_ids = fields.Many2many('openacademy.session',
    #                                string="Sessions", readonly=True)
