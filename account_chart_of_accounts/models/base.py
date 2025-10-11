from odoo import models, fields, api, _


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        kwargs.update({
            'limit': 1000,
        })
        return super(Base, self).search_panel_select_range(field_name, **kwargs)