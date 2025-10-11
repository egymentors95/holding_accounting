from odoo import fields, models, api, _
from odoo.osv import expression
import re


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = 'product.category'
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    supplier_code = fields.Char(
        string='Supplier Code',
        help='The code used by the supplier to identify this product.',
        copy=True,
    )
    oracle_code = fields.Char(
        string='Oracle Code',
        help='The code used by Oracle to identify this product.',
        copy=True,
    )

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not name or any(term[0] == 'id' for term in (args or [])):
            return super(ProductTemplate, self)._name_search(
                name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
            )

        Product = self.env['product.product']
        templates = self.browse([])
        while True:
            domain = templates and [('product_tmpl_id', 'not in', templates.ids)] or []
            args = args if args is not None else []
            kwargs = {} if limit else {'limit': None}

            search_domain = expression.OR([
                args + domain,
                [('supplier_code', operator, name)],
                [('oracle_code', operator, name)],
            ])

            product_ids = Product._name_search(
                name, search_domain, operator=operator,
                name_get_uid=name_get_uid, **kwargs
            )
            products = Product.browse(product_ids)
            new_templates = products.mapped('product_tmpl_id')
            if new_templates & templates:
                break
            templates |= new_templates
            if (not products) or (limit and (len(templates) > limit)):
                break

        searched_ids = set(templates.ids)

        tmpl_without_variant_ids = []
        if not limit or len(searched_ids) < limit:
            tmpl_without_variant_ids = self.env['product.template'].search(
                [('id', 'not in', self.env['product.template']._search([('product_variant_ids.active', '=', True)]))]
            )
        if tmpl_without_variant_ids:
            domain = expression.AND([args or [], [('id', 'in', tmpl_without_variant_ids.ids)]])
            searched_ids |= set(super(ProductTemplate, self)._name_search(
                name,
                args=domain,
                operator=operator,
                limit=limit,
                name_get_uid=name_get_uid))

        return super(ProductTemplate, self)._name_search(
            '', args=[('id', 'in', list(searched_ids))],
            operator='ilike', limit=limit, name_get_uid=name_get_uid
        )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(
                    self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(
                        self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('supplier_code', '=', name)] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(
                        self._search([('oracle_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))

            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(
                        args + [('name', operator, name), ('id', 'not in', product_ids)],
                        limit=limit2,
                        access_rights_uid=name_get_uid
                    )
                    product_ids.extend(product2_ids)

                if not limit or len(product_ids) < limit:
                    limit3 = (limit - len(product_ids)) if limit else False
                    supplier_code_ids = self._search(
                        args + [('supplier_code', operator, name), ('id', 'not in', product_ids)],
                        limit=limit3,
                        access_rights_uid=name_get_uid
                    )
                    product_ids.extend(supplier_code_ids)

                if not limit or len(product_ids) < limit:
                    limit4 = (limit - len(product_ids)) if limit else False
                    oracle_code_ids = self._search(
                        args + [('oracle_code', operator, name), ('id', 'not in', product_ids)],
                        limit=limit4,
                        access_rights_uid=name_get_uid
                    )
                    product_ids.extend(oracle_code_ids)

            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))

            if not product_ids and operator in positive_operators:
                ptrn = re.compile(r'(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search(
                        [('default_code', '=', res.group(2))] + args,
                        limit=limit,
                        access_rights_uid=name_get_uid
                    ))
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)

        return product_ids
