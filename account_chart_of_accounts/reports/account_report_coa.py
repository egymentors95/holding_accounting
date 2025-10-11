# -*- coding: utf-8 -*-

import io
from copy import deepcopy
from collections import defaultdict
from odoo import models, fields, api, _
from odoo.tools.misc import xlsxwriter, formatLang


class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = "account.coa.report"

    filter_full_hierarchy = True

    @api.model
    def format_value(self, amount, currency=False, blank_if_zero=False):
        ''' Format amount to have a monetary display (with a currency symbol).
        E.g: 1000 => 1000.0 $

        :param amount:          A number.
        :param currency:        An optional res.currency record.
        :param blank_if_zero:   An optional flag forcing the string to be empty if amount is zero.
        :return:                The formatted amount as a string.
        '''
        currency_id = currency or self.env.company.currency_id
        if currency_id.is_zero(amount):
            amount = abs(amount)

        if self.env.context.get('no_format'):
            return amount
        return formatLang(self.env, amount, currency_obj=currency_id)

    @api.model
    def _init_filter_full_hierarchy(self, options, previous_options=None):
        if previous_options and 'full_hierarchy' in previous_options:
            options['full_hierarchy'] = previous_options['full_hierarchy']
        else:
            options['full_hierarchy'] = self.filter_full_hierarchy

    # Create codes path in the hierarchy based on account.
    def get_parent_account_codes(self, account):
        # A code is tuple(id, name)
        codes = []
        if account.parent_id:
            parent = account.parent_id
            while parent:
                codes.append((parent.id, '%s %s' % (parent.code, parent.name)))
                parent = parent.parent_id
        else:
            codes.append((0, _('(No Parent)')))
        return list(reversed(codes))

    @api.model
    def _create_full_hierarchy(self, lines, options):
        """Compute the hierarchy based on account parents when the option is activated.

        The option is available only when there are account.group for the company.
        It should be called when before returning the lines to the client/templater.
        The lines are the result of _get_lines(). If there is a hierarchy, it is left
        untouched, only the lines related to an account.account are put in a hierarchy
        according to the account.group's and their prefixes.
        """
        unfold_all = self.env.context.get('print_mode') and len(options.get('unfolded_lines')) == 0 or options.get('unfold_all')

        def add_to_hierarchy(lines, key, level, parent_id, hierarchy):
            val_dict = hierarchy[key]
            unfolded = val_dict['id'] in options.get('unfolded_lines') or unfold_all
            # add the group totals
            lines.append({
                'id': val_dict['id'],
                'name': val_dict['name'],
                'title_hover': val_dict['name'],
                'unfoldable': True,
                'unfolded': unfolded,
                'level': level,
                'parent_id': parent_id,
                'columns': [{'name': self.format_value(c) if isinstance(c, (int, float)) else c, 'no_format_name': c} for c in val_dict['totals']],
                'name_class': 'o_account_report_name_ellipsis top-vertical-align'
            })
            if not self._context.get('print_mode') or unfolded:
                # add every direct child group recursively
                for child in val_dict['children_codes']:
                    add_to_hierarchy(lines, child, level + 1, val_dict['id'], hierarchy)
                # add all the lines that are in this group but not in one of this group's children groups
                for l in val_dict['lines']:
                    l['level'] = level + 1
                    l['parent_id'] = val_dict['id']
                lines.extend(val_dict['lines'])

        def compute_full_hierarchy(lines, level, parent_id):
            # put every line in each of its parents (from less global to more global) and compute the totals
            hierarchy = defaultdict(lambda: {'totals': [None] * len(lines[0]['columns']), 'lines': [], 'children_codes': set(), 'name': '', 'parent_id': None, 'id': ''})
            for line in lines:
                account = self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('id'))))
                codes = self.get_parent_account_codes(account)  # id, name
                for code in codes:
                    hierarchy[code[0]]['id'] = 'hierarchy_' + str(code[0])
                    hierarchy[code[0]]['name'] = code[1]
                    for i, column in enumerate(line['columns']):
                        if 'no_format_name' in column:
                            no_format = column['no_format_name']
                        elif 'no_format' in column:
                            no_format = column['no_format']
                        else:
                            no_format = None
                        if isinstance(no_format, (int, float)):
                            if hierarchy[code[0]]['totals'][i] is None:
                                hierarchy[code[0]]['totals'][i] = no_format
                            else:
                                hierarchy[code[0]]['totals'][i] += no_format
                for code, child in zip(codes[:-1], codes[1:]):
                    hierarchy[code[0]]['children_codes'].add(child[0])
                    hierarchy[child[0]]['parent_id'] = hierarchy[code[0]]['id']
                hierarchy[codes[-1][0]]['lines'] += [line]
            # compute the tree-like structure by starting at the roots (being account without parents)
            hierarchy_lines = []
            for root in [k for k, v in hierarchy.items() if not v['parent_id']]:
                add_to_hierarchy(hierarchy_lines, root, level, parent_id, hierarchy)
            return hierarchy_lines

        new_lines = []
        account_lines = []
        current_level = 0
        parent_id = 'root'
        for line in lines:
            if not (line.get('caret_options') == 'account.account' or line.get('account_id')):
                # make the hierarchy with the lines we gathered, append it to the new lines and restart the gathering
                if account_lines:
                    new_lines.extend(compute_full_hierarchy(account_lines, current_level + 1, parent_id))
                account_lines = []
                new_lines.append(line)
                current_level = line['level']
                parent_id = line['id']
            else:
                # gather all the lines we can create a hierarchy on
                account_lines.append(line)
        # do it one last time for the gathered lines remaining
        if account_lines:
            new_lines.extend(compute_full_hierarchy(account_lines, current_level + 1, parent_id))
        return new_lines


    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)

        render_values = {
            'report': {
                'name': self._get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.company.name,
            },
            'options': options,
            'context': self.env.context,
            'model': self,
        }
        if additional_context:
            render_values.update(additional_context)

        # Create lines/headers.
        if line_id:
            headers = options['headers']
            lines = self._get_lines(options, line_id=line_id)
            template = templates['line_template']
        else:
            headers, lines = self._get_table(options)
            options['headers'] = headers
            template = templates['main_template']
        if options.get('hierarchy'):

            lines = self._create_hierarchy(lines, options)
        if options.get('full_hierarchy'):
            account_ids = [l['id'] for l in lines if type(l['id']) == int]
            extended_accounts = self.env['account.account'].search([('id', 'not in', account_ids),
                                                                    ('child_ids','=', False)])
            no_col = len(lines[0]['columns'])

            for acc in extended_accounts:
                name = '%s %s' % (acc.code, acc.name)
                lines.insert(0,{
                    'id': acc.id,
                    'name': name,
                    'title_hover': name,
                    'columns': [ {'name': self.format_value(0), 'class': 'number', 'no_format_name': 0.0}] * no_col,
                    'unfoldable': False,
                    #'level': acc.level,
                    'caret_options': 'account.account',
                    'class': 'o_account_searchable_line o_account_coa_column_contrast'
                })

            lines = self._create_full_hierarchy(lines, options)

            lines = sorted(lines, key=lambda i: i['name'].split()[0])
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)
        render_values['lines'] = {'columns_header': headers, 'lines': lines}

        # Manage footnotes.
        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        # Render.
        html = self.env.ref(template)._render(render_values)
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html

    @api.model
    def _get_columns(self, options):
        header1 = [
            {'name': '', 'style': 'width:40%'},
            {'name': _('Initial Balance'), 'class': 'number', 'colspan': 2},
        ] + [
            {'name': period['string'], 'class': 'number', 'colspan': 2}
            for period in reversed(options['comparison'].get('periods', []))
        ] + [
            {'name': options['date']['string'], 'class': 'number', 'colspan': 2},
            {'name': _('Total'), 'class': 'number', 'colspan': 2},
        ]
        header2 = [
            {'name': '', 'style': 'width:40%'},
            {'name': _('Debit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
        ]
        if options.get('comparison') and options['comparison'].get('periods'):
            header2 += [
                {'name': _('Debit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
                {'name': _('Credit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
            ] * len(options['comparison']['periods'])
        header2 += [
            {'name': _('Debit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Debit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
            {'name': _('Credit'), 'width': 15, 'class': 'number o_account_coa_column_contrast'},
        ]
        return [header1, header2]

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        date_default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'bold': True,'font_size': 12, 'font_color': '#666666'})

        #Set the first column width to 50
        sheet.set_column(0, 0, 50)

        y_offset = 0
        headers, lines = self._get_table(options)

        # Add headers.
        for header in headers:
            x_offset = 0
            for column in header:
                column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                colspan = column.get('colspan', 1)
                if column.get('width'):
                    sheet.set_column(y_offset, x_offset, column.get('width'))
                if colspan == 1:
                    sheet.write(y_offset, x_offset, column_name_formated, title_style)
                else:
                    sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated, title_style)
                x_offset += colspan
            y_offset += 1

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('full_hierarchy'):
            account_ids = [l['id'] for l in lines if type(l['id']) == int]
            extended_accounts = self.env['account.account'].search(
                [('id', 'not in', account_ids), ('child_ids', '=', False)])
            no_col = len(lines[0]['columns'])
            for acc in extended_accounts:
                name = '%s %s' % (acc.code, acc.name)
                lines.insert(0, {
                    'id': acc.id,
                    'name': name,
                    'title_hover': name,
                    'columns': [{'name': self.format_value(0), 'class': 'number', 'no_format_name': 0.0}] * no_col,
                    'unfoldable': False,
                    # 'level': acc.level,
                    'caret_options': 'account.account',
                    'class': 'o_account_searchable_line o_account_coa_column_contrast'
                })

            lines = self._create_full_hierarchy(lines, options)
            lines = sorted(lines, key=lambda i: i['name'].split()[0])
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        # Add lines.
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
                col1_style =  workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': level - 1})
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'bold': True,})
                col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'bold': True,'indent': level - 1})

            #write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            #write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
