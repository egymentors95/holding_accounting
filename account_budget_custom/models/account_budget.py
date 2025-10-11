from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"
    _order = "create_date desc"

    reserved_percent = fields.Float(string='Reserved Percent')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True, required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    crossovered_budget_line = fields.One2many(copy=False)

    def unlink(self):
        for budget in self:
            if budget.state not in 'draft':
                raise UserError(_('You can not delete budget not in draft state'))
        return super(CrossoveredBudget, self).unlink()

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (copy)',
            'state': 'draft',
        })
        return super(CrossoveredBudget, self).copy(default)

    # check that budget period doesn't overlap with another budget
    @api.constrains('crossovered_budget_line', 'date_from', 'date_to')
    def _check_budget_line_period(self):
        for budget in self:
            if budget.state == 'done':
                continue
            for line in budget.crossovered_budget_line:
                domain = [
                    ('crossovered_budget_id.date_from', '<=', budget.date_to),
                    ('crossovered_budget_id.date_to', '>=', budget.date_from),
                    ('crossovered_budget_id.state', '=', 'done'),
                    ('id', '!=', line.id),
                    ('analytic_account_id', '=', line.analytic_account_id.id),
                    ('general_budget_id', '=', line.general_budget_id.id),
                ]
                if self.env['crossovered.budget.lines'].search_count(domain):
                    raise ValidationError(_('Budget lines can not be overlaped with another.'))


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    reserved_percent = fields.Float(related='crossovered_budget_id.reserved_percent', string='Reserved Percent')
    reserved_amount = fields.Float(string='Reserved Amount', readonly=True, compute='_compute_reserved_amount')
    pull_out = fields.Monetary(string='Pull Out', compute='_compute_pull_out',
                               help=_('Amount of money that has been pulled out'),store=False)

    provide = fields.Float(string='Provide', compute='_compute_provide',
                           help=_('Amount of money that has been provided'),store=False)

    remain = fields.Float(string='Remain of Christening', compute='_compute_remain',help=_('Amount of money that has been remained'))
    above_remain = fields.Float(string='Exceed Amount', compute='_compute_remain',
                                help=_('Amount of money that has been exceeded'))
    purchase_remain = fields.Float(store=True)
    practical_amount = fields.Float(compute='_compute_practical_amount', string='Practical Amount', digits=0,
                                    store=False, help=_('Total amount of money that has been spent'))
    theoritical_amount = fields.Float(compute='_compute_theoritical_amount', string='Theoretical Amount', digits=0,
                                      store=True)
    percentage = fields.Float(compute='_compute_percentage', string='Achievement', store=False, digits=(16, 4))
    from_operation_ids = fields.One2many('budget.operations', 'from_budget_line_id', string='From Operation')
    to_operation_ids = fields.One2many('budget.operations', 'to_budget_line_id', string='Cost Center')
    year_end = fields.Boolean(compute="get_year_end")

    final_amount = fields.Float(string='Final Amount', compute='_compute_final_amount',
                                help=_('Final amount of money that has been provided'),store=False)

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

    @api.depends('planned_amount', 'provide', 'pull_out')
    def _compute_final_amount(self):
        for rec in self:
            rec.final_amount = rec.planned_amount + rec.provide + rec.pull_out

    @api.depends('from_operation_ids')
    def _compute_pull_out(self):
        for line in self:
            operations = self.env['budget.operations'].search(
                [('from_budget_line_id', '=', line.id), ('state', '=', 'confirmed')])

            pull_out = sum(op.amount + op.purchase_remind for op in
                           operations.filtered(lambda x: x.state == 'confirmed') if
                           op.operation_type == 'transfer' or op.operation_type == 'decrease')
            line.pull_out = pull_out if line.planned_amount < 0 else pull_out * -1

    @api.depends('to_operation_ids')
    def _compute_provide(self):
        for line in self:
            operations = self.env['budget.operations'].search(
                [('to_budget_line_id', '=', line.id), ('state', '=', 'confirmed')])

            provide = sum(op.amount + op.purchase_remind for op in
                          operations.filtered(lambda x: x.state == 'confirmed') if
                          op.operation_type == 'transfer' or op.operation_type == 'increase')
            line.provide = provide * -1 if line.planned_amount < 0 else provide

    @api.depends('to_operation_ids', 'from_operation_ids')
    def _compute_remain(self):
        for line in self:
            remain_value = ((abs(line.final_amount) - abs(line.reserve) - abs(line.confirm) - abs(
                line.practical_amount)) * -1)
            line.remain = 0 if remain_value > 0 else remain_value
            line.above_remain = remain_value if remain_value > 0 else 0

    def get_year_end(self):
        for rec in self:
            date = fields.Date.today()
            if rec.crossovered_budget_id.date_to <= date and rec.purchase_remain > 0:
                rec.year_end = True
            else:
                rec.year_end = False

    def transfer_budget_action(self):
        formview_ref = self.env.ref('account_budget_custom.view_budget_operations', False)
        return {
            'name': ("Budget Transfer"),
            'view_mode': ' form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'budget.operations',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'views': [(formview_ref and formview_ref.id or False, 'form')],
            'context': {
                'default_operation_type': 'transfer',
                'default_from_budget_post_id': self.general_budget_id.id,
                'default_from_crossovered_budget_id': self.crossovered_budget_id.id,
                'default_from_budget_line_id': self.id,
                'default_purchase_remind': self.purchase_remain,
                'default_date': fields.Date.today(),
            }
        }

    @api.depends('analytic_account_id', 'planned_amount', 'practical_amount')
    def name_get(self):
        result = []

        for line in self:
            name = ''
            name += line.analytic_account_id and line.analytic_account_id.name or '' + ' ' + _('remaining') + ' '
            name += str(line.final_amount)

            result.append((line.id, name))
        return result

    # @api.depends('crossovered_budget_id.reserved_percent')
    def _compute_reserved_amount(self):
        for line in self:
            reserved_amount = line.crossovered_budget_id.reserved_percent * \
                              line.planned_amount / 100.0
            if reserved_amount:
                reserved_amount -= line.with_context({'reserved': True}).pull_out
            line.reserved_amount = reserved_amount

    def _compute_practical_amount(self):
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get(
                'wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.general_budget_id.account_ids.ids),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to)
                          ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    def _check_amount(self, amount=0, purchase_remind=0, transfer=False):
        for obj in self:
            reserved_amount = obj.crossovered_budget_id.reserved_percent * \
                              obj.planned_amount / 100.0

            if obj.with_context({'reserved': True}).pull_out > reserved_amount:
                raise ValidationError(
                    _('''You can not take more than the reserved amount.'''))

            if transfer and abs(obj.remain) < abs(purchase_remind):
                raise ValidationError(
                    _('''You can not take more than the remaining amount..'''))

            if amount and amount > obj.remain:
                raise ValidationError(
                    _('''You can not take more than the remaining amount..'''))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_sale_orders(self):
        self.ensure_one()
        sale_order_ids = self._get_sale_orders().ids
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
        if len(sale_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': sale_order_ids[0],
            })
        else:
            action.update({
                'name': _('Sources Sale Orders %s', self.name),
                'domain': [('id', 'in', sale_order_ids)],
                'view_mode': 'tree,form',
            })
        return action
