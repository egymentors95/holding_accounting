# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from hijri_converter import convert
from num2words import num2words


class AccountMove(models.Model):
    _inherit = "account.move"

    def compute_hijri_date(self, date):
        if date:
            date = datetime.datetime.strptime(str(date), '%Y-%m-%d')
            year = date.year
            day = date.day
            month = date.month
            hijri_date = convert.Gregorian(year, month, day).to_hijri()
            return hijri_date

class AccountPayment(models.Model):
    _inherit = "account.payment"


    @api.depends('amount')
    def amount_to_words(self):
        for rec in self:
            if rec.amount:
                rec.text_amount = num2words(
                    rec.amount, to='currency', lang='ar')

    def compute_hijri_date(self, date):
        if date:
            date = datetime.datetime.strptime(str(date), '%Y-%m-%d')
            year = date.year
            day = date.day
            month = date.month
            hijri_date = convert.Gregorian(year, month, day).to_hijri()
            return hijri_date

    text_amount = fields.Char(string="Total In Words",required=False, compute="amount_to_words")

