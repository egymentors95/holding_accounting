from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    # def _account_entry_move(self, qty, description, svl_id, cost):
    #     pass


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # _sql_constraints = [
    #     ('name_uniq', 'unique(name, company_id)', 'Reference must be unique per Company!'),
    #     ('qty_positive', 'check(product_qty <= 0)', 'The quantity to produce must be positive!'),
    # ]
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        help='The asset associated with this production order.', domain="[('method', '=', 'product_quantity')]",
        states={'draft': [('readonly', False)]}
    )

    @api.constrains('asset_id')
    def _check_quantity(self):
        for record in self:
            if record.asset_id and record.product_qty > record.asset_id.product_qty:
                raise ValidationError(
                    _('The quantity must be Lower than or Equal Asset quantity'))

    def _create_custom_account_move(self):
        for order in self:
            journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)

            account_total_debit = self.env['account.account'].search([('code', '=', '110700100001')], limit=1)

            cost_of_stock = sum([
                move.quantity_done * move.product_id.standard_price
                for move in order.move_raw_ids
            ])

            total_labor = sum([
                (wo.duration / 60.0) * wo.workcenter_id.labor_costs
                for wo in order.workorder_ids if wo.workcenter_id.labor_costs
            ])
            total_electricity = sum([
                (wo.duration / 60.0) * wo.workcenter_id.electricity_costs
                for wo in order.workorder_ids if wo.workcenter_id.electricity_costs
            ])
            total_rental = sum([
                (wo.duration / 60.0) * wo.workcenter_id.rental_costs
                for wo in order.workorder_ids if wo.workcenter_id.rental_costs
            ])
            total_other_costs = total_labor + total_electricity + total_rental
            total_cost = cost_of_stock + total_other_costs

            move_lines = [
                (0, 0, {
                    'account_id': account_total_debit.id,
                    'debit': total_cost,
                    'credit': 0.0,
                    'name': f"Production Cost - {order.name}",
                }),
            ]

            def get_share(part):
                return (part / total_cost) * total_cost if total_cost else 0.0

            if cost_of_stock:
                move_lines.append((0, 0, {
                    'account_id': self.env['account.account'].search([('code', '=', '110700100005')], limit=1).id,
                    'debit': 0.0,
                    'credit': cost_of_stock,
                    'name': "Raw Materials",
                }))
            if total_labor:
                labor_account = order.workorder_ids.mapped('workcenter_id.labor_account_id')[:1]
                if labor_account:
                    move_lines.append((0, 0, {
                        'account_id': labor_account.id,
                        'debit': 0.0,
                        'credit': total_labor,
                        'name': "Labor Cost",
                    }))
            if total_electricity:
                electricity_account = order.workorder_ids.mapped('workcenter_id.electricity_account_id')[:1]
                if electricity_account:
                    move_lines.append((0, 0, {
                        'account_id': electricity_account.id,
                        'debit': 0.0,
                        'credit': total_electricity,
                        'name': "Electricity Cost",
                    }))
            if total_rental:
                rental_account = order.workorder_ids.mapped('workcenter_id.rental_account_id')[:1]
                if rental_account:
                    move_lines.append((0, 0, {
                        'account_id': rental_account.id,
                        'debit': 0.0,
                        'credit': total_rental,
                        'name': "Rental Cost",
                    }))

            account_move = self.env['account.move'].create({
                'journal_id': journal.id,
                'ref': f"MO: {order.name}",
                'date': fields.Date.today(),
                'line_ids': move_lines,
            })
            account_move.action_post()



class MrpImmediateProduction(models.TransientModel):
    _inherit = 'mrp.immediate.production'
    depreciation_move_ids = fields.One2many('account.move', 'asset_id', string='Depreciation Lines', readonly=True,
                                            states={'draft': [('readonly', False)], 'open': [('readonly', False)],
                                                    'paused': [('readonly', False)]})

    def process(self):
        productions_to_do = self.env['mrp.production']
        productions_not_to_do = self.env['mrp.production']

        for line in self.immediate_production_line_ids:
            if line.to_immediate:
                productions_to_do |= line.production_id
            else:
                productions_not_to_do |= line.production_id

        for production in productions_to_do:
            error_msg = ""
            if production.product_tracking in ('lot', 'serial') and not production.lot_producing_id:
                production.action_generate_serial()

            if production.product_tracking == 'serial' and float_compare(
                    production.qty_producing, 1, precision_rounding=production.product_uom_id.rounding) == 1:
                production.qty_producing = 1
            else:
                production.qty_producing = production.product_qty - production.qty_produced

            production._set_qty_producing()

            for move in production.move_raw_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                rounding = move.product_uom.rounding
                for move_line in move.move_line_ids:
                    if move_line.product_uom_qty:
                        move_line.qty_done = min(move_line.product_uom_qty, move_line.move_id.should_consume_qty)
                    if float_compare(move.quantity_done, move.should_consume_qty, precision_rounding=rounding) >= 0:
                        break
                if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=rounding) == 1:
                    if move.has_tracking in ('serial', 'lot'):
                        error_msg += "\n  - %s" % move.product_id.display_name

            if error_msg:
                raise UserError(_('You need to supply Lot/Serial Number for products:') + error_msg)

            mrp_id = production
            asset_id = mrp_id.asset_id
            material_move_lines = []
            indirect_cost_move_lines = []
            journal = asset_id.journal_id.id or self.env['account.journal'].search(
                [('name', '=', 'Miscellaneous Journal')], limit=1).id
            date = mrp_id.date_planned_start

            for move in mrp_id.move_raw_ids:
                value = move.product_uom_qty * move.product_id.standard_price
                material_move_lines.append((0, 0, {
                    'name': move.product_id.display_name,
                    'account_id': move.product_id.categ_id.property_stock_valuation_account_id.id,
                    'credit': value,
                    'debit': 0.0,
                    'product_id': move.product_id.id,
                    'quantity': move.quantity_done,
                }))
                material_move_lines.append((0, 0, {
                    'name': move.product_id.display_name,
                    'account_id': move.product_id.categ_id.property_account_expense_categ_id.id,
                    'debit': value,
                    'credit': 0.0,
                    'product_id': move.product_id.id,
                    'quantity': move.quantity_done,
                }))

            total_indirect = 0.0
            indirect_cost_move_lines = []

            for workorder in mrp_id.workorder_ids:
                wc = workorder.workcenter_id
                if wc.labor_costs:
                    indirect_cost_move_lines.append((0, 0, {
                        'name': _('Labor - %s') % wc.name,
                        'account_id': wc.labor_account_id.id,
                        'credit': wc.labor_costs,
                        'debit': 0.0,
                    }))
                    total_indirect += wc.labor_costs
                if wc.electricity_costs:
                    indirect_cost_move_lines.append((0, 0, {
                        'name': _('Electricity - %s') % wc.name,
                        'account_id': wc.electricity_account_id.id,
                        'credit': wc.electricity_costs,
                        'debit': 0.0,
                    }))
                    total_indirect += wc.electricity_costs
                if wc.rental_costs:
                    indirect_cost_move_lines.append((0, 0, {
                        'name': _('Rental - %s') % wc.name,
                        'account_id': wc.rental_account_id.id,
                        'credit': wc.rental_costs,
                        'debit': 0.0,
                    }))
                    total_indirect += wc.rental_costs

            if total_indirect > 0:
                indirect_cost_move_lines.append((0, 0, {
                    'name': _('Indirect Cost Valuation for %s') % mrp_id.name,
                    'account_id': mrp_id.product_id.categ_id.property_stock_valuation_account_id.id,
                    'debit': total_indirect,
                    'credit': 0.0,
                }))

            # if indirect_cost_move_lines:
            #     entry=self.env['account.move'].create({
            #         'move_type': 'entry',
            #         'date': mrp_id.date_planned_start,
            #         'journal_id': self.env['account.journal'].search([('name', '=', 'Miscellaneous Journal')],
            #                                                          limit=1).id,
            #         'ref': _('Indirect Cost Entry for %s') % mrp_id.name,
            #         'line_ids': indirect_cost_move_lines,
            #     })
            #     entry.action_post()
            total_indirect = sum([
                wc.labor_costs + wc.electricity_costs + wc.rental_costs
                for wc in mrp_id.workorder_ids.mapped('workcenter_id')
            ])

            if total_indirect:
                indirect_cost_move_lines.append((0, 0, {
                    'name': _('Total Indirect Cost - %s') % mrp_id.name,
                    'account_id': mrp_id.product_id.categ_id.property_stock_valuation_account_id.id,
                    'debit': total_indirect,
                    'credit': 0.0,
                }))

            if asset_id:
                asset_id.total_depreciation_entries_count += 1
                asset = asset_id.depreciation_move_ids.create({
                    'asset_id': asset_id.id,
                    'ref': asset_id.name,
                    'move_type': 'entry',
                    'date': fields.Date.context_today(self),
                    'journal_id': asset_id.journal_id.id,
                    'line_ids': [(0, 0, {
                        'name': asset_id.name,
                        'account_id': asset_id.account_depreciation_id.id,
                        'credit': mrp_id.product_qty * asset_id.product_price,
                        'debit': 0.0,
                    }), (0, 0, {
                        'name': _('Depreciation for %s', asset_id.name),
                        'account_id': asset_id.account_depreciation_expense_id.id,
                        'credit': 0.0,
                        'debit': mrp_id.product_qty * asset_id.product_price,
                    })],
                    'amount_total': mrp_id.product_qty * asset_id.product_price,
                    'asset_depreciated_value': sum(asset_id.depreciation_move_ids.mapped('asset_depreciated_value')) + (
                            mrp_id.product_qty * asset_id.product_price),
                    'asset_remaining_value': asset_id.value_residual - (
                            mrp_id.product_qty * asset_id.product_price),

                })
                asset.action_post()

            if material_move_lines:
                entry1 = self.env['account.move'].create({
                    'move_type': 'entry',
                    'date': date,
                    'journal_id': journal,
                    'ref': _('Raw Material Entry for %s') % mrp_id.name,
                    'line_ids': material_move_lines,
                })
                entry1.action_post()
            # if indirect_cost_move_lines:
            #     entry2=self.env['account.move'].create({
            #         'move_type': 'entry',
            #         'date': date,
            #         'journal_id': journal,
            #         'ref': _('Indirect Cost Entry for %s') % mrp_id.name,
            #         'line_ids': indirect_cost_move_lines,
            #     })
            #     entry2.action_post()
        mrp_id._create_custom_account_move()
        productions_to_validate = self.env.context.get('button_mark_done_production_ids')
        if productions_to_validate:
            productions_to_validate = self.env['mrp.production'].browse(productions_to_validate)
            productions_to_validate = productions_to_validate - productions_not_to_do
            return productions_to_validate.with_context(skip_immediate=True).button_mark_done()
        return True


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    duration = fields.Float(
        'Real Duration Per Minute', compute='_compute_duration', inverse='_set_duration',
        readonly=False, store=True, copy=False)

    @api.depends('time_ids.duration', 'qty_produced')
    def _compute_duration(self):
        for order in self:
            order.duration = sum(order.time_ids.mapped('duration'))
            order.duration_unit = round(order.duration / max(order.qty_produced, 1),
                                        2)  # rounding 2 because it is a time
            if order.duration_expected:
                order.duration_percent = max(-2147483648, min(2147483647, 100 * (
                        order.duration_expected - order.duration) / order.duration_expected))
            else:
                order.duration_percent = 0


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    labor_costs = fields.Float(
        string='Labor Costs',
        help='The cost of labor associated with this work center.',
        default=0.0)
    labor_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Labor Account',
        help='The account used for labor costs associated with this work center.',
        domain="[('deprecated', '=', False)]",
        default=lambda self: self.env['account.account'].search([('code', '=', '700000')], limit=1)
    )
    electricity_costs = fields.Float(
        string='Electricity Costs',
        help='The cost of Electricity associated with this work center.',
        default=0.0)
    electricity_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Electricity Account',
        help='The account used for electricity costs associated with this work center.',
        domain="[('deprecated', '=', False)]",
        default=lambda self: self.env['account.account'].search([('code', '=', '700001')], limit=1))
    rental_costs = fields.Float(
        string='Rental Costs',
        help='The cost of Rental associated with this work center.',
        default=0.0)
    rental_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Rental Account',
        help='The account used for rental costs associated with this work center.',
        domain="[('deprecated', '=', False)]",
        default=lambda self: self.env['account.account'].search([('code', '=', '700002')], limit=1))
    costs_hour = fields.Float(string='Cost per hour', help='Specify cost of work center per hour.', default=0.0,
                              compute='_compute_costs_hour', store=True, readonly=False)

    @api.depends('labor_costs', 'electricity_costs', 'rental_costs')
    def _compute_costs_hour(self):
        for record in self:
            record.costs_hour = record.labor_costs + record.electricity_costs + record.rental_costs


# class MrpBom(models.Model):
#     _inherit = 'mrp.bom'

    # _sql_constraints = [
    #     ('qty_positive', 'check (product_qty < 0)', 'The quantity to produce must be positive!'),
    # ]
