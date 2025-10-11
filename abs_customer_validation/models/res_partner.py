# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2022-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit="res.partner"

    def get_partner_list(self,partner_objs):
        partner_list = ''
        for partner in partner_objs:
            partner_list = partner_list + ' || ' + partner.name
        return partner_list

    @api.onchange('name')
    def onchange_name(self):
        if self.name and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            if self.env['res.partner'].search([('name','=',self.name)]):
                raise ValidationError(_('The record ' +self.name+' is already exist '))

    @api.onchange('phone')
    def onchange_phonenumber(self):
        if self.phone and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            partner_objs = self.env['res.partner'].search([('phone','=',self.phone)])
            if self.get_partner_list(partner_objs):
                raise ValidationError(_('Phone number '+str(self.phone)+' is already exist in the following records:' + '\n' + self.get_partner_list(partner_objs)))

    @api.onchange('mobile')
    def onchange_mobilenumber(self):
        if self.mobile and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            partner_objs = self.env['res.partner'].search([('mobile','=',self.mobile)])
            if self.get_partner_list(partner_objs):
                raise ValidationError(_('Mobile number '+str(self.mobile)+' is already exist in the following records:' + '\n' + self.get_partner_list(partner_objs)))

    @api.onchange('fax')
    def onchange_fax(self):
        if self.fax and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            partner_objs = self.env['res.partner'].search([('fax','=',self.fax)])
            if self.get_partner_list(partner_objs):
                raise ValidationError(_('Fax number '+str(self.fax)+' is already exist in the following records:' + '\n' + self.get_partner_list(partner_objs)))

    @api.onchange('email')
    def onchange_email(self):
        if self.email and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            partner_objs = self.env['res.partner'].search([('email','=',self.email)])
            if self.get_partner_list(partner_objs):
                raise ValidationError(_('Email number '+str(self.email)+' is already exist in the following records:' + '\n' + self.get_partner_list(partner_objs)))

    @api.onchange('website')
    def onchange_website(self):
        if self.website and self.user_has_groups("abs_customer_validation.group_activate_customer_validation"):
            website_id = "http://"+str(self.website)
            partner_objs = self.env['res.partner'].search([('website','=',website_id)])
            if self.get_partner_list(partner_objs):
                raise ValidationError(_('Website number '+str(self.website)+' is already exist in the following records:' + '\n' + self.get_partner_list(partner_objs)))


