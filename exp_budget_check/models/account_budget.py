from odoo import api, fields, models, _


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    reserve = fields.Float(string='Reserve Amount', compute='_compute_reserve',
                           help=_('Total amount of reserved purchase orders'))
    confirm = fields.Float(string='Confirm Amount', compute='_compute_confirm',
                           help=_('Total amount of confirmed purchase orders'))

    @api.depends('analytic_account_id')
    def _compute_confirm(self):
        for rec in self:
            order_lines = self.env['purchase.order.line'].search(
                [('account_analytic_id', '=', rec.analytic_account_id.id),
                 ('order_id.date_order', '>=', rec.crossovered_budget_id.date_from),
                 ('order_id.date_order', '<=', rec.crossovered_budget_id.date_to),
                 '|', ('product_id.property_account_expense_id', 'in', rec.general_budget_id.account_ids.ids),
                 ('product_id.categ_id.property_account_expense_categ_id', 'in', rec.general_budget_id.account_ids.ids),
                 ('order_id.state', 'in', ['purchase', 'done'])])
            orders_without_tax = sum(order_lines.mapped('price_subtotal'))
            need_tax = 0
            invoice_amount = 0
            for line in order_lines:
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.filtered(lambda x: x.analytic).compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'])
                need_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                invoiced = self.env['account.move.line'].search(
                    [('purchase_line_id', '=', line.id), ('move_id.state', 'not in', ['draft', 'cancel'])])
                invoice_amount += sum(invoiced.mapped('price_subtotal')) if not need_tax else sum(
                    invoiced.mapped('move_id.amount_total'))
            rec.confirm = ((orders_without_tax + need_tax) - invoice_amount) * -1

    @api.depends('analytic_account_id')
    def _compute_reserve(self):
        for rec in self:
            order_lines = self.env['purchase.order.line'].search(
                [('account_analytic_id', '=', rec.analytic_account_id.id),
                 ('order_id.date_order', '>=', rec.crossovered_budget_id.date_from),
                 ('order_id.date_order', '<=', rec.crossovered_budget_id.date_to),
                 '|', ('product_id.property_account_expense_id', 'in', rec.general_budget_id.account_ids.ids),
                 ('product_id.categ_id.property_account_expense_categ_id', 'in', rec.general_budget_id.account_ids.ids),
                 ('order_id.state', 'in', ['draft', 'sent', 'to approve'])])
            orders_without_tax = sum(order_lines.mapped('price_subtotal'))
            need_tax = 0
            for line in order_lines:
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.filtered(lambda x: x.analytic).compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'])
                need_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            rec.reserve = (orders_without_tax + need_tax) * -1

    def _compute_operations_amount(self):
        if not self.ids: return
        for line in self:
            pull_out = provide = budget_confirm_amount = 0.0
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get(
                'wizard_date_from') or line.date_from

            if line.analytic_account_id.id:
                if 'reserved' not in self.env.context:
                    self.env.cr.execute("""
                           SELECT SUM(amount)
                           FROM budget_operations
                           WHERE from_budget_line_id=%s
                               AND (date between %s AND %s)
                               AND state='confirmed'""",
                                        (line.id, date_from, date_to,))
                    pull_out = self.env.cr.fetchone()[0] or 0.0

                if 'reserved' in self.env.context:
                    self.env.cr.execute("""
                           SELECT SUM(amount)
                           FROM budget_operations
                           WHERE from_budget_line_id=%s
                               AND (date between %s AND %s)
                               AND state='confirmed' 
                               AND from_reserved=%s""",
                                        (line.id, date_from, date_to, self.env.context['reserved']))
                    pull_out = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("""
                       SELECT SUM(amount)
                       FROM budget_operations
                       WHERE to_budget_line_id=%s
                           AND (date between %s AND %s)
                           AND state='confirmed'""",
                                    (line.id, date_from, date_to,))
                provide = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("""
                       SELECT SUM(amount)
                       FROM budget_confirmation_line
                       WHERE budget_line_id=%s
                           AND (date between %s AND %s)
                           AND state='done'""",
                                    (line.id, date_from, date_to,))
                budget_confirm_amount = self.env.cr.fetchone()[0] or 0.0

            line.budget_confirm_amount = budget_confirm_amount
