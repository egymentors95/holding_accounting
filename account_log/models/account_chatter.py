# -*- coding: utf-8 -*-

from odoo import api, models, _


class ResCurrency(models.Model):
    _name = 'res.currency'
    _inherit = ['res.currency', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_') or f == 'id']
        for x in dels:
            del fields[x]
        return set(fields)

class CurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    @api.model
    def create(self, values):
        body = _("<p>Currency Rate created</p><ul>")
        fields = self.fields_get()
        for k, v in values.items():
            field = fields.get(k)
            if field['type'] == 'selection':
                val = dict(field['selection'])[v]
            elif field['type'] == 'many2one':
                val = self.env[field['relation']].sudo().browse(v).name_get()[0][1]
            else:
                val = v
            body += "<li>%s: %s</li>" % (field['string'], val)
        body += "</ul>"
        self.env['mail.message'].create({
            'body': body,
            'model': 'res.currency',
            'res_id': self._context.get('active_id'),
            'subtype_id': '2',
        })
        return super(CurrencyRate, self).create(values)

    def write(self, values):
        body = _("<p>Currency Rate updated</p><ul>")
        fields = self.fields_get()
        old_values = self.read(values.keys())[0]
        for k, v in values.items():
            field = fields.get(k)
            if field['type'] == 'selection':
                val = dict(field['selection'])[v]
                old_val = dict(field['selection'])[old_values[k]]
            elif field['type'] == 'many2one':
                val = self.env[field['relation']].sudo().browse(v).name_get()[0][1]
                old_val = old_values[k][1]
            else:
                val = v
                old_val = old_values[k]
            body += "<li>%s: %s -> %s</li>" % (field['string'], old_val, val)
        body += "</ul>"
        self.env['mail.message'].create({
            'body': body,
            'model': 'res.currency',
            'res_id': self.currency_id.id,
            'subtype_id': '2',
        })
        return super(CurrencyRate, self).write(values)

    def unlink(self):
        self.env['mail.message'].create({
            'body': _("<p>Currency Rate deleted</p>"),
            'model': 'res.currency',
            'res_id': self.currency_id.id,
            'subtype_id': '2',
        })
        return super(CurrencyRate, self).unlink()


class AccountTax(models.Model):
    _name = 'account.tax'
    _inherit = ['account.tax', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_') or f == 'id']
        for x in dels:
            del fields[x]
        return set(fields)


class AccountPaymentTerm(models.Model):
    _name = 'account.payment.term'
    _inherit = ['account.payment.term', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_') or f == 'id']
        for x in dels:
            del fields[x]
        return set(fields)


class AccountPaymentTermLine(models.Model):
    _inherit = 'account.payment.term.line'

    @api.model
    def create(self, values):
        body = _("<p>Payment Term Lines created</p><ul>")
        fields = self.fields_get()
        for k, v in values.items():
            field = fields.get(k)
            if field['type'] == 'selection':
                val = dict(field['selection'])[v]
            elif field['type'] == 'many2one':
                val = self.env[field['relation']].sudo().browse(v).name_get()[0][1]
            else:
                val = v
            body += "<li>%s: %s</li>" % (field['string'], val)
        body += "</ul>"
        self.env['mail.message'].create({
            'body': body,
            'model': 'account.payment.term',
            'res_id': values.get('payment_id'),
            'subtype_id': '2',
        })
        return super(AccountPaymentTermLine, self).create(values)

    def write(self, values):
        body = _("<p>Payment Term Lines updated</p><ul>")
        fields = self.fields_get()
        old_values = self.read(values.keys())[0]
        for k, v in values.items():
            field = fields.get(k)
            if field['type'] == 'selection':
                val = dict(field['selection'])[v]
                old_val = dict(field['selection'])[old_values[k]]
            elif field['type'] == 'many2one':
                val = self.env[field['relation']].sudo().browse(v).name_get()[0][1]
                old_val = old_values[k][1]
            else:
                val = v
                old_val = old_values[k]
            body += "<li>%s: %s -> %s</li>" % (field['string'], old_val, val)
        body += "</ul>"
        self.env['mail.message'].create({
            'body': body,
            'model': 'account.payment.term',
            'res_id': self.payment_id.id,
            'subtype_id': '2',
        })
        return super(AccountPaymentTermLine, self).write(values)

    def unlink(self):
        self.env['mail.message'].create({
            'body': _("<p>Payment Term Lines deleted</p>"),
            'model': 'account.payment.term',
            'res_id': self.payment_id.id,
            'subtype_id': '2',
        })
        return super(AccountPaymentTermLine, self).unlink()


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_')
                or f in ('id', 'kanban_dashboard', 'kanban_dashboard_graph', 'json_activity_data')]
        for x in dels:
            del fields[x]
        return set(fields)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_') or f == 'id' or f == 'string_to_hash']
        for x in dels:
            del fields[x]
        return set(fields)