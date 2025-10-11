from odoo import models, fields, api
import logging

from odoo.exceptions import UserError, Warning


_logger = logging.getLogger(__name__)

class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    @api.model
    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        try:
            res = super(AccountChartTemplate, self)._load(sale_tax_rate, purchase_tax_rate, company)
            return res
        except Warning as e:
            error_message = f"Error during _load: {e.name if hasattr(e, 'name') else str(e)}"
            _logger.error(error_message)
            raise Warning(error_message)


    # @api.model
    # def try_loading(self, *args, **kwargs):
    #     try:
    #         return super(AccountChartTemplate, self).try_loading(*args, **kwargs)
    #     except Warning as e:
    #         error_message = f"Error during try_loading: {e.name if hasattr(e, 'name') else str(e)}"
    #         _logger.error(error_message)
    #         raise Warning(error_message)
