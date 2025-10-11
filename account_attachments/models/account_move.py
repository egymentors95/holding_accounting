# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):

    _inherit = 'account.move'

    attach_no = fields.Integer(compute='get_attachments')
    res_id = fields.Integer()
    res_model = fields.Char()

    # def get_attachments(self):
    #     # Check if multiple records are passed, and handle them in a loop
    #     if len(self) > 1:
    #         action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
    #         action['domain'] = [
    #             ('res_model', '=', 'account.move'),
    #             ('res_id', 'in', self.ids),
    #         ]
    #
    #         # Update attachment count for all records (if necessary)
    #         for record in self:
    #             related_ids = record.ids
    #             related_models = ['account.move']
    #
    #             if record.res_id and record.res_model:
    #                 related_ids = record.ids + [record.res_id]
    #                 related_models.append(record.res_model)
    #                 action['domain'] = [
    #                     ('res_model', 'in', related_models),
    #                     ('res_id', 'in', related_ids),
    #                 ]
    #
    #             # Context for creating new attachments for each record
    #             action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (record._name, record.id)
    #
    #             # Update attachment count for each record
    #             record.attach_no = self.env['ir.attachment'].search_count([
    #                 ('res_model', 'in', related_models),
    #                 ('res_id', 'in', related_ids)
    #             ])
    #
    #         return action
    #
    #     # If only one record is passed, use the original logic
    #     self.ensure_one()
    #
    #     action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
    #     action['domain'] = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in', self.ids),
    #     ]
    #     domain = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in', self.ids),
    #     ]
    #     related_ids = self.ids
    #     related_models = ['account.move']
    #
    #     if self.res_id and self.res_model:
    #         related_ids = self.ids + [self.res_id]
    #         related_models.append(self.res_model)
    #         action['domain'] = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids),
    #         ]
    #         domain = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids),
    #         ]
    #
    #     # Context for creating new attachments
    #     action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
    #
    #     # Update attachment count for smart button
    #     self.attach_no = self.env['ir.attachment'].search_count(domain)
    #
    #     return action

    def get_attachments(self):
        # Check if multiple records are passed, and handle them in a loop
        Attachment = self.env['ir.attachment']
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')

        if len(self) > 1:
            print("Multiple records mode")
            all_models_ids = set()

            for record in self:
                related_pairs = set()

                # Main record
                related_pairs.add((record._name, record.id))

                # Purchase Order
                if record.purchase_id:
                    related_pairs.add((record.purchase_id._name, record.purchase_id.id))

                    # Request ID
                    if record.purchase_id.request_id:
                        related_pairs.add((record.purchase_id.request_id._name, record.purchase_id.request_id.id))

                    # Requisition ID (only if it's the expected model)
                    if record.purchase_id.requisition_id and record.purchase_id.requisition_id._name == 'purchase.requisition':
                        related_pairs.add(('purchase.requisition', record.purchase_id.requisition_id.id))

                # Accumulate all related model-id pairs
                all_models_ids.update(related_pairs)

            # Build domain from accumulated pairs
            domain = []
            pairs = list(all_models_ids)
            if pairs:
                domain = ['|'] * (len(pairs) - 1)
                for model, res_id in pairs:
                    domain.extend(['&', ('res_model', '=', model), ('res_id', '=', res_id)])

            # Use the first record for context
            action['domain'] = domain
            action['context'] = {
                'default_res_model': self[0]._name,
                'default_res_id': self[0].id,
            }

            for record in self:
                record.attach_no = Attachment.search_count([
                    ('res_model', '=', record._name),
                    ('res_id', '=', record.id)
                ])
            return action

        # If only one record is passed, use the original logic
        self.ensure_one()
        self_model = self._name
        print("22222222222")

        related_pairs = []

        # Current record
        related_pairs.append((self_model, self.id))

        # Request record
        if self.purchase_id:
            related_pairs.append((self.purchase_id._name, self.purchase_id.id))

        if self.purchase_id.request_id:
                    related_pairs.append((self.purchase_id.request_id._name, self.purchase_id.request_id.id))

        # Requisition record (only if exact model match)
        if self.purchase_id.requisition_id and self.purchase_id.requisition_id._name == 'purchase.requisition':
            related_pairs.append(('purchase.requisition', self.purchase_id.requisition_id.id))

        # Build domain with explicit pairs
        domain = []
        if related_pairs:
            domain = ['|'] * (len(related_pairs) - 1)
            for model, res_id in related_pairs:
                domain.extend([
                    '&',
                    ('res_model', '=', model),
                    ('res_id', '=', res_id)
                ])
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = domain
        action['context'] = {
            'default_res_model': self_model,
            'default_res_id': self.id,
        }
        self.attach_no = self.env['ir.attachment'].search_count(domain)

        return action


    # def get_attachments(self):
    #     self.ensure_one()

    #     action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
    #     action['domain'] = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in',self.ids), ]
    #     domain = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in', self.ids), ]
    #     related_ids = self.ids
    #     related_models = 'account.move'

    #     if self.res_id and self.res_model:
    #         related_ids = self.ids + [self.res_id]
    #         related_models = ['account.move', self.res_model]
    #         action['domain'] = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids), ]
    #         domain = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids), ]

    #     # Context for creating new attachments
    #     action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
    #     # Update attachment count for smart button


    #     self.attach_no = self.env['ir.attachment'].search_count(domain)

    #     return action

