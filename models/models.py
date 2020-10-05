# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import timedelta, date

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

    courses_ids = fields.Many2one('openacademy.department',
                                ondelete='cascade', string="Courses", required=True)

    department_id = fields.Many2one('openacademy.department', string="Department", required=True)

    chef_id = fields.Many2one('res.partner', string="Chef Department")


    def _default_courses(self):
        my_courses = self.env['openacademy.course'].search_count([])
        values['my_courses'] = my_courses


    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
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
    courses_ids = fields.One2many('openacademy.course', 'courses_ids',string="Courses", required=True)
    sessions_ids = fields.Many2many('openacademy.session', string="Department", required=True)

    def btn_ord(self):

        lines = []
        for session in self.sessions_ids:

            line ={
                'product_id': session.id,
                'name': session.name,
                'product_uom_qty': session.duration,
                'price_unit': session.pu,
            }

            lines.append(line)

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
                                            ('category_id.name', 'ilike', "Teacher")])

    # course_id = fields.Many2one('openacademy.course',
    #                             ondelete='cascade', string="Course", required=True)

    course_id = fields.Many2many('openacademy.course',
                                ondelete='cascade', string="Course", required=True)

    sessions_ids = fields.Many2one('openacademy.department',
                                 ondelete='cascade', string="Department", required=True)

    department_id = fields.Many2many('openacademy.department', string="Department", required=True)

    chef_id = fields.Many2one('res.partner', string="Chef Department")

    # session have many attendees(res.partner) and attendee can participate in many sessions
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    def get_portal_url(self):
        portal_link = "session/%s" % (self.id+1)
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

class Report(models.Model):
    _name = 'openacademy.report'
    _description = "OpenAcademy Report"
    _auto = False

    instru = fields.Many2one('res.partner', string="Instructor") #id many2one et remplacé id dans field de view... (voir pivot de session)
    session_name = fields.Char(readonly=True)
    courseid = fields.Many2one('openacademy.course', string="Course")
    course_name = fields.Char(readonly=True)
    sessionsid = fields.Many2one('openacademy.session', string="Session")
    responsible = fields.Char(readonly=True)
    #aussi resoudre probléme de session unique pour chaque cours

    def init(self):

        self._cr.execute("""
        CREATE OR REPLACE VIEW openacademy_report AS (
        Select row_number() over() as id, d.id as courseid, d.name as course_name, d.responsible_id as responsible,r.id as sessionsid , r.name as session_name, r.instructor_id as instru
        from openacademy_course as d 
        inner join openacademy_session as r
        on r.course_id = d.id
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
