from odoo import models, api, fields
import urllib.parse
import base64


class WhatsappSendMessage(models.TransientModel):
    _name = 'whatsapp.message.wizard'
    _description = "Whatsapp Wizard"

    user_id = fields.Many2one('res.partner', string="Recipient")
    mobile = fields.Char(related='user_id.mobile', required=True)
    message = fields.Text(string="Message", required=True)
    invoice_id = fields.Many2one('account.move', string="Invoice")

    def send_message(self):
        if self.message and self.mobile:
            if self.invoice_id:
                pdf_content, _ = self.env.ref('account.account_invoices')._render_qweb_pdf(self.invoice_id.id)
                attachment = self.env['ir.attachment'].create({
                    'name': f'Invoice_{self.invoice_id.name}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.move',
                    'res_id': self.invoice_id.id,
                    'mimetype': 'application/pdf',
                })
                download_url = f"/web/content/{attachment.id}?download=true"
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                public_link = f"{base_url}{download_url}"

                self.message += f"\n\nDownload your invoice here: {public_link}"

            message_encoded = urllib.parse.quote(self.message)
            return {
                'type': 'ir.actions.act_url',
                'url': f"https://api.whatsapp.com/send?phone={self.user_id.mobile}&text={message_encoded}",
                'target': 'new',
                'res_id': self.id,
            }
