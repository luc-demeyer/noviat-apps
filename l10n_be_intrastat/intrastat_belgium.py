# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012-14 Agaplan (www.agaplan.eu) & Noviat (www.noviat.com).
#    All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from csv import writer as csvwriter
from base64 import b64encode
from datetime import datetime
import logging
_logger = logging.getLogger('l10n_be_intrastat')


def get_start_date(*args, **kwargs):
    # Don't like dateutil, not in the python battery pack
    now = datetime.today()
    try:
        # Rewind the month and set first of month
        now = now.replace(day=1, month=now.month - 1)
    except ValueError:
        # Means we have to rewind to last year
        _logger.debug("had to rewind start_dat to last year, had exception",
                      exc_info=True)
        now = now.replace(
            day=1,
            month=now.month + 11,
            year=now.year - 1
        )
    return now.strftime('%Y-%m-%d')


class intrastat_belgium(orm.Model):
    _name = 'report.intrastat.belgium'
    _rec_name = 'start_date'
    _order = 'start_date desc, ttype'

    def _compute_numbers(self, cr, uid, ids, name, arg, context=None):
        return self.pool.get('report.intrastat.common')._compute_numbers(
            cr, uid, ids, self, context=context)

    def _compute_total_fiscal_amount(self, cr, uid, ids,
                                     name, arg, context=None):
        result = {}
        for intrastat in self.browse(cr, uid, ids, context=context):
            total_fiscal_amount = 0.0
            for line in intrastat.intrastat_line_ids:
                total_fiscal_amount += line.amount_company_currency * \
                    line.intrastat_type_id.fiscal_value_multiplier
            result[intrastat.id] = total_fiscal_amount
        return result

    def _compute_end_date(self, cr, uid, ids, name, arg, context=None):
        res = self.pool.get('report.intrastat.common')._compute_dates(
            cr, uid, ids, self, context=context)
        res.update({k: res[k]['end_date'] for k in res})
        return res

    def _get_intrastat_from_line(self, cr, uid, ids, context=None):
        return self.pool.get('report.intrastat.belgium').search(
            cr, uid, [('intrastat_line_ids', 'in', ids)], context=context)

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            states={'done': [('readonly', True)]},
            help="Related company."),
        'start_date': fields.date(
            'Start date', required=True,
            states={'done': [('readonly', True)]},
            help="Start date of the declaration. Must be "
            "the first day of a month."),
        'end_date': fields.function(
            _compute_end_date, method=True, type='date', string='End date',
            store={'report.intrastat.belgium': (
                   lambda self, cr, uid, ids, c={}: ids, ['start_date'], 10
                   )},
            help="End date for the declaration. "
            "Is the last day of the month of the start date."),
        'date_done': fields.datetime(
            'Date done', readonly=True,
            help="Last date when the intrastat declaration was "
            "converted to 'Done' state."),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('edit', 'Edit'),
            ('done', 'Done'),
            ], 'State', select=True, readonly=True,
            help="State of the declaration. When the state is set to 'Done', "
            "the parameters become read-only."),
        'extended': fields.boolean(
            'Extended Declaration',
            states={'done': [('readonly', True)]},
            help="Is the declaration an extended one ?"),
        'ttype': fields.selection([
            ('A', 'Arrival (19)'),
            ('D', 'Departure (29)')
            ], 'Type', required=True,
            states={'done': [('readonly', True)]},
            help="Select the type of report."),
        'revision': fields.integer(
            'Revision', readonly=True,
            help="Used to keep track of unique changes"),
        'intrastat_line_ids': fields.one2many(
            'report.intrastat.belgium.line', 'parent_id',
            'Belgium intrastat product lines',
            states={'done': [('readonly', True)]}),
        'num_lines': fields.function(
            _compute_numbers, method=True,
            type='integer', multi='numbers',
            string='Number of lines',
            store={'report.intrastat.belgium.line': (
                   _get_intrastat_from_line, ['parent_id'], 20
                   )},
            help="Number of lines in this declaration."),
        'total_amount': fields.function(
            _compute_numbers, method=True,
            string='Total amount',
            type='float', digits=(16, 0), multi='numbers',
            store={'report.intrastat.belgium.line': (
                   _get_intrastat_from_line,
                   ['amount_company_currency', 'parent_id'], 20
                   )},
            help="Total amount in company currency of the declaration."),
        'currency_id': fields.related(
            'company_id', 'currency_id', readonly=True,
            type='many2one', relation='res.currency', string='Currency'),
        'notes': fields.text(
            'Notes',
            help="You can add some comments here if you want."),
    }

    _defaults = {
        'state': 'draft',
        'ttype': 'D',
        'revision': 1,
        'start_date': get_start_date,
        'company_id': lambda self, cr, uid, ct:
            self.pool.get('res.users')._get_company(cr, uid, ct),
    }

    _sql_constraints = [
        ('date_uniq',
         'unique(start_date, company_id, ttype)',
         'A declaration of the same type already exists for this month !'),
    ]

    def copy(self, cr, uid, ids, default=None, context=None):
        if 'intrastat_line_ids' not in default:
            default['intrastat_line_ids'] = []
        if 'start_date' not in default:
            default['start_date'] = False
        if 'revision' not in default:
            default['revision'] = False
        return super(intrastat_belgium, self).copy(
            cr, uid, ids, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        res = super(intrastat_belgium, self).write(
            cr, uid, ids, vals, context)
        if 'skip_revision' not in context:
            cr.execute(
                "UPDATE report_intrastat_belgium "
                "SET revision=revision+1 WHERE id in (%s)",
                [tuple(ids)])
        return res

    def _find_stock_links(self, cr, uid, invoice_line, context=None):
        sm_obj = self.pool.get('stock.move')
        sale_line = self.pool.get('sale.order.line')
        if sale_line:
            cr.execute("""
        SELECT sm.id
        FROM sale_order_line_invoice_rel solir
        INNER JOIN stock_move sm ON (sm.sale_line_id = solir.order_line_id)
        WHERE solir.invoice_id = %s
            """, (invoice_line.invoice_id.id,))
            stock_ids = [x[0] for x in cr.fetchall()]
            _logger.debug("found stock moves: %s", stock_ids)
            return sm_obj.browse(cr, uid, stock_ids, context=context)
        return []

    def _find_invoice_links(self, cr, uid, stock_line, context=None):
        res_invoices = []
        res_lines = []
        if hasattr(stock_line, 'sale_line_id'):
            if stock_line.sale_line_id:
                res_lines.extend(stock_line.sale_line_id.invoice_lines)
                res_invoices.extend(
                    stock_line.sale_line_id.order_id.invoice_ids)
        if hasattr(stock_line, 'purchase_line_id'):
            if stock_line.purchase_line_id:
                res_lines.extend(stock_line.purchase_line_id.invoice_lines)
                res_invoices.extend(
                    stock_line.purchase_line_id.order_id.invoice_ids)
        res_invoices = list(set(res_invoices))
        res_lines = list(set(res_lines))
        return res_invoices, res_lines

    def _get_intrastat(self, cr, uid, product, context=None):
        intrastat = False
        if product.type not in ['product', 'consu'] or \
                product.exclude_from_intrastat:
            return intrastat
        intrastat = product.intrastat_id or \
            product.categ_id.intrastat_id

        p_name = product.name + (
            product.default_code and
            (' (ref: ' + product.default_code
             + ')') or '')
        if not intrastat:
            raise orm.except_orm(
                _('Configuration Error !'),
                _("No 'Intrastat Code' defined for "
                  "a product of type Stockable or Consumable."
                  "\nPlease review the Intrastat settings for "
                  "Product '%s' (Intrastat code '%s'.")
                % (p_name, intrastat.intrastat_code))
        """
        Nettogewicht is optioneel voor producten
        waarvoor 'aanvullende eenheden' verplicht zijn
        Cf. NBB document Gecombineerde Nomenclatuur,
        kolom "Bijzondere maatstaf"
        """
        if not intrastat.intrastat_uom_id and \
                not isinstance(product.weight_net, float):
            raise orm.except_orm(
                _('Configuration Error !'),
                _("No 'Net Weight' defined for "
                  "a product without Intrastat UOM."
                  "\nPlease review the Intrastat settings for "
                  "Product '%s' (Intrastat code '%s'.")
                % (p_name, intrastat.intrastat_code))
        return intrastat

    def _gather_invoices(self, cr, uid, declaration, context=None):
        """ Search invoices between start_date and end_date of declaration """
        decl_lines = []
        cur_obj = self.pool.get('res.currency')
        inv_obj = self.pool.get('account.invoice')

        inv_ids = inv_obj.search(cr, uid, [
            ('date_invoice', '>=', declaration.start_date),
            ('date_invoice', '<=', declaration.end_date),
            ('state', 'in', ['open', 'paid']),
            ('company_id', '=', declaration.company_id.id),
        ], context=context)
        _logger.debug("found %d invoices: %s", len(inv_ids), inv_ids)
        for invoice in inv_obj.browse(cr, uid, inv_ids, context=context):
            if not invoice.partner_id.country_id:
                _logger.debug(
                    "invoice %s partner had no country, "
                    "assuming same country as company and skipping",
                    invoice.number)
                continue
            if not invoice.partner_id.country_id.intrastat:
                _logger.debug(
                    "invoice %s partner was in country "
                    "that doesnt require intrastat reporting",
                    invoice.number)
                continue
            if invoice.partner_id.country_id == \
                    declaration.company_id.partner_id.country_id:
                _logger.debug(
                    "invoice %s had same country of origin as company",
                    invoice.number)
                continue

            if declaration.ttype == 'A' and \
                    invoice.type in ['out_invoice', 'in_refund']:
                # Wrong declaration type for this sort of invoices
                continue
            elif declaration.ttype == 'D' and \
                    invoice.type in ['in_invoice', 'out_refund']:
                # Wrong declaration type for this sort of invoices
                continue

            trans_type = {
                'out_invoice': 1,
                'in_invoice': 1,
                'out_refund': 2,
                'in_refund': 2,
            }.get(invoice.type)

            for inv_line in invoice.invoice_line:
                # To DO:
                # add check on tax code:
                # add entry to note field if intracom to warn the user
                product = inv_line.product_id
                if not product:
                    _logger.debug("invoice line did not have a product")
                    continue

                intrastat = self._get_intrastat(cr, uid, product, context)
                if not intrastat:
                    continue

                line_value = inv_line.price_subtotal
                if invoice.currency_id.id != \
                        declaration.company_id.currency_id.id:
                    # Convert the value to the company currency
                    line_value = cur_obj.compute(
                        cr, uid, invoice.currency_id.id,
                        declaration.company_id.currency_id.id, line_value,
                        context=context)

                if intrastat.intrastat_uom_id:
                    quantity = str(int(round(inv_line.quantity)))
                else:
                    quantity = None

                decl_lines.append((0, 0, {
                    'parent_id': declaration.id,
                    'invoice_id': invoice.id,
                    'invoice_line_id': inv_line.id,
                    'country_id': invoice.partner_id.country_id.id,
                    'product_id': product.id,
                    'intrastat_id': intrastat.id,
                    'intrastat_code': intrastat.intrastat_code,
                    'weight': str(int(round(
                        product.weight_net * inv_line.quantity))),
                    'quantity': quantity,
                    'region': declaration.company_id.intrastat_belgium_region,
                    'amount_company_currency': int(round(line_value)),
                    'transaction': trans_type,
                    'extnr': invoice.number[-13:],
                }))
            _logger.debug(
                "invoice %s gave us following intrastat lines: %s",
                invoice.number, decl_lines)
        return decl_lines

    def _gather_stock(self, cr, uid, declaration, context=None):
        """
        Search stock moves between date
        (not invoiced on invoices processed before)
        To find the link requires that
        'sale' or 'purchase' module is installed ?
        """
        decl_lines = []
        sm_obj = self.pool.get('stock.move')

        # Perhaps search on pickings where intrastat_declare
        # is False so we can use this as extra filter?

        stock_ids = sm_obj.search(cr, uid, [
            ('date', '>=', declaration.start_date),
            ('date', '<=', declaration.end_date),
            ('state', 'not in', ['draft', 'cancel']),
            ('intrastat_declare', '=', True),
            ('company_id', '=', declaration.company_id.id),
        ], context=context)

        for move in sm_obj.browse(cr, uid, stock_ids, context=context):
            if move.picking_id:
                if not move.picking_id.intrastat_declare:
                    _logger.debug(
                        "stock move %d part of picking "
                        "that should not be declared %d",
                        move.id, move.picking_id.id)
                    continue

            country = move.partner_id.country_id or \
                move.picking_id.partner_id.country_id
            country = move.picking_id.intrastat_country_id or country
            if not country:
                _logger.debug(
                    "assuming no country means "
                    "same as company country, so skipped")
                continue
            if not country.intrastat:
                _logger.debug(
                    "stock move was from/to country "
                    "that doesnt require intrastat reporting")
                continue
            if country == declaration.company_id.partner_id.country_id:
                _logger.debug("stock move was from/to same country as company")
                continue

            product = move.product_id
            intrastat = self._get_intrastat(cr, uid, product, context)
            if not intrastat:
                continue

            value = move.price_unit or product.list_price
            ref = move.picking_id and move.picking_id.name or '%d [%s] %s' \
                % (move.id, product.default_code, product.name)

            invoices, inv_lines = self._find_invoice_links(
                cr, uid, move, context)

            trans_type = False
            if move.location_id.usage == 'internal' and \
                    move.location_dest_id.usage in ['supplier', 'customer']:
                _logger.debug("stock move deemed to be a delivery")
                if declaration.ttype == 'D':
                    # TODO: handle the special case when company doesnt do
                    # delivery declarations but does do the arrival
                    trans_type = 1
                else:
                    # Skip line wrong type of declaration
                    continue
            elif move.location_dest_id.usage == 'internal' and \
                    move.location_id.usage in ['supplier', 'customer']:
                _logger.debug("stock move deemed to be arrival")
                if declaration.ttype == 'A':
                    # TODO: handle the special case when company doesnt do
                    # arrival declarations but does do the departure
                    trans_type = 1
                else:
                    # Skip line wrong type of declaration
                    continue
            else:
                # Doesnt seem to be arriving or leaving, ignore the line
                _logger.warn(
                    "stock move %d from %s to %s ignored",
                    move.id, move.location_id.name,
                    move.location_dest_id.name)
                continue

            # Now we overwrite the trans_type if specified on the move line
            if move.intrastat_transaction:
                trans_type = int(move.intrastat_transaction)

            if intrastat.intrastat_uom_id:
                quantity = move.intrastat_qty or \
                    str(int(round(move.product_qty)))
            else:
                quantity = None

            decl_lines.append((0, 0, {
                'parent_id': declaration.id,
                'invoice_id': invoices and invoices[0].id,
                'invoice_line_id': inv_lines and inv_lines[0].id,
                'picking_id': move.picking_id and move.picking_id.id or False,
                'move_id': move.id,
                'country_id': country.id,
                'product_id': product.id,
                'intrastat_id': intrastat and intrastat.id,
                'intrastat_code': intrastat.intrastat_code,
                'weight': move.intrastat_weight or str(int(round(
                    product.weight_net * move.product_qty))),
                'quantity': quantity,
                'region': declaration.company_id.intrastat_belgium_region,
                'amount_company_currency': int(round(
                    value * move.product_qty)),
                'transaction': trans_type,
                'extnr': ref[:13],
            }))
        return decl_lines

    def action_gather(self, cr, uid, ids, context=None):
        context = context or {}
        _logger.debug("gathering lines for declarations: %s", ids)

        # Call function which will update the lines,
        # preferably in one write operation so the revision number
        # does not go up much (or even nothing)
        for declaration in self.browse(cr, uid, ids, context=context):
            # Should we clear [(6,0,[])] previous lines ?
            decl_lines_init = [(6, 0, [])]
            decl_lines = decl_lines_init[:]
            if declaration.company_id.data_source == 'move':
                decl_lines += self._gather_stock(
                    cr, uid, declaration, context)
            elif declaration.company_id.data_source == 'invoice':
                decl_lines += self._gather_invoices(
                    cr, uid, declaration, context)
            else:
                raise orm.except_orm(
                    _("Programming Error !"),
                    _("Please report this issue via your "
                      "OpenERP support channel."))

            if decl_lines == decl_lines_init:
                raise orm.except_orm(
                    _('No Data Available'),
                    _('No records found for the selected period!'))

            # Store intrastat lines
            declaration.write({
                'intrastat_line_ids': decl_lines,
            }, context=context)

        # Now when we update state it should not increase the revision number
        context.update({'skip_revision': True})
        return self.write(cr, uid, ids, {'state': 'edit'}, context=context)

    def action_send(self, cr, uid, ids, context=None):
        context = context or {}
        # Create itx file + send (maybe ask email to send from ?)

        itx_buffer = StringIO()
        itx_file = csvwriter(itx_buffer, delimiter=';')

        today = datetime.today()
        for declaration in self.browse(cr, uid, ids, context=context):
            decl_date = datetime.strptime(
                declaration.start_date, "%Y-%m-%d")
            vat_no = declaration.company_id.partner_id.vat
            if not vat_no:
                raise orm.except_orm(
                    _('Data Insufficient'),
                    _('No VAT Number Associated with Main Company!'))
            vat_no = vat_no.replace(' ', '').upper()
            itx_head = [
                # Field 1: Identification declarant
                # (10 digit company number or 9 digit VAT number)
                vat_no[2:],
                # Field 2, Field 3: Third party VAT number + zip code
                '',
                '',
                # Field 4 : Declaration id
                '%s%s' % (
                    str(declaration.id).zfill(4)[-4:],
                    str(declaration.revision).zfill(4)[-4:]),
            ]

            lines_all = []
            for intrastat_line in declaration.intrastat_line_ids:

                if declaration.extended:
                    if not intrastat_line.incoterm:
                        raise orm.except_orm(
                            _("Missing incoterm"),
                            _("The line with source reference %s "
                              "has no incoterm selected")
                            % intrastat_line.extnr)
                    if not intrastat_line.transport:
                        raise orm.except_orm(
                            _("Missing transport"),
                            _("The line with source reference %s "
                              "has no transport selected")
                            % intrastat_line.extnr)

                lines_all.append({
                    'match': [
                        # Field 10
                        intrastat_line.country_code,
                        # Field 11
                        intrastat_line.transport or '',
                        # Field 12
                        intrastat_line.transaction,
                        # Field 13
                        intrastat_line.intrastat_code.replace(' ', ''),
                        # Field 18
                        declaration.currency_id.name,
                        # Field 19
                        intrastat_line.incoterm or '',
                        # Field 20
                        intrastat_line.region,
                        ],
                    'vals': [
                        # Field 14
                        int(intrastat_line.weight),
                        # Field 15
                        int(intrastat_line.quantity),
                        # Field 16
                        intrastat_line.amount_company_currency,
                        ],
                    })

            # combine similar records
            lines_combined = []
            for i in range(len(lines_all)):
                similar = False
                for j in range(len(lines_combined)):
                    if lines_all[i]['match'] == lines_combined[j]['match']:
                        similar = True
                        lines_combined[j] = {
                            'match': lines_combined[j]['match'],
                            'vals': map(
                                lambda x, y: x + y, lines_all[i]['vals'],
                                lines_combined[j]['vals']),
                            }
                if not similar:
                    lines_combined.append(lines_all[i])

            itx_lines = map(
                lambda x: x['match'][:4] + x['vals'] + [''] + x['match'][-3:],
                lines_combined)
            line_count = 0
            for line in itx_lines:
                line_count += 1
                itx_line = list(itx_head) + [
                    line_count,  # Field 5
                    1,  # Field 6
                    today.strftime('%y%m%d'),  # Field 7
                    decl_date.strftime('%y%m'),  # Field 8
                    declaration.ttype,  # Field 9
                    ] + line
                itx_file.writerow(itx_line)

            filename = '%s%02d%s%s.itx' % (
                {'A': 19, 'D': 29}[declaration.ttype],
                decl_date.month,
                str(declaration.id).zfill(2)[-2:],
                str(declaration.revision).zfill(2)[-2:],
            )

            self.pool.get('ir.attachment').create(
                cr, uid, {
                    'res_id': declaration.id,
                    'res_model': self._name,
                    'name': filename,
                    'datas': b64encode(itx_buffer.getvalue()),
                }, context=context)

        # Sending the file should again not increase revision
        context.update({'skip_revision': True})
        return self.write(
            cr, uid, ids, {
                'state': 'done',
                'date_done': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            }, context=context)

    def action_reset(self, cr, uid, ids, context=None):
        context = context or {}
        context.update({'skip_revision': True})
        return self.write(
            cr, uid, ids, {
                'state': 'draft',
                'date_done': False},
            context=context)

    def onchange_company_or_ttype(self, cr, uid, ids,
                                  company_id, ttype, context=None):
        res = {'value': {}}
        if company_id:
            company = self.pool.get('res.company').browse(
                cr, uid, company_id, context=context)
            if not company.intrastat_belgium:
                raise orm.except_orm(
                    _("Configuration Error"),
                    _("The selected company is not configured "
                      "to declare belgian intrastat"),
                )
        if company_id and ttype:
            extended = False
            if ttype == 'A':
                if not company.intrastat_belgium_arrival:
                    raise orm.except_orm(
                        _("Configuration Error"),
                        _("The selected company is not configured "
                          "to send arrival declarations"),
                    )
                else:
                    extended = company.intrastat_belgium_arrival_extended
            elif ttype == 'D':
                if not company.intrastat_belgium_departure:
                    raise orm.except_orm(
                        _("Configuration Error"),
                        _("The selected company is not configured "
                          "to send departure declarations"),
                    )
                else:
                    extended = company.intrastat_belgium_departure_extended
            res['value'].update({'extended': extended})
        _logger.debug("Result: %s", res)
        return res


class intrastat_belgium_line(orm.Model):
    _name = 'report.intrastat.belgium.line'

    _columns = {
        'parent_id': fields.many2one(
            'report.intrastat.belgium', 'Intrastat product ref',
            ondelete='cascade', readonly=True),
        'state': fields.related(
            'parent_id', 'state', type='char', string='State'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice ref', readonly=True),
        'invoice_line_id': fields.many2one(
            'account.invoice.line', 'Invoice line', readonly=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking ref', readonly=True),
        'move_id': fields.many2one(
            'stock.move', 'Stock move', readonly=True),
        'country_id': fields.many2one(
            'res.country', 'Country of origin/destination',
            states={'done': [('readonly', True)]}),
        'incoterm_id': fields.many2one(
            'stock.incoterms', 'Incoterm',
            states={'done': [('readonly', True)]}),
        'product_id': fields.many2one(
            'product.product', 'Product',
            states={'done': [('readonly', True)]}),
        'intrastat_id': fields.many2one(
            'report.intrastat.code', 'Intrastat Code',
            required=True, states={'done': [('readonly', True)]}),

        # Field 1: Declaring party VAT number (10 fixed XX)
        #          (using vat number from company_id defined in header)
        # Field 2: Third party declarant (14 variable XX) (will be left empty)
        # Field 3: Zip code (5 variable XX) (will be left empty)
        # Field 4: Retnr (8 variable 99) declaration id
        #          (built using decl id (4 chars)/revision(4 chars) of header)
        # Field 5: Line nr (5 variable 99) generated on the fly
        # Field 6: Message function (1/5/0) default 1
        # Field 7: Declaration date (will be generated on the fly)
        # Field 8: Period (will be generated from start_date in header)
        # Field 9: Flow (direction, already defined in header as 'ttype')
        # Field 10: Land van herk/best (2 fixed XX)
        'country_code': fields.related(
            'country_id', 'code', type='char', size=2,
            string='Product country of origin/destination', readonly=True),
        # Field 11: Tranport (1 fixed 99)
        'transport': fields.selection([
            (1, 'Transport by sea'),
            (2, 'Transport by rail'),
            (3, 'Transport by road'),
            (4, 'Transport by air'),
            (5, 'Consignments by post'),
            (7, 'Fixed transport installations'),
            (8, 'Transport by inland waterway'),
            (9, 'Own propulsion'),
            ], 'Type of transport', states={'done': [('readonly', True)]}),
        # Field 12: Transaction type (1 variable 99)
        'transaction': fields.integer(
            'Transaction Type', required=True,
            states={'done': [('readonly', True)]}),
        # Field 13: GN8 Code (8 fixed 99)
        'intrastat_code': fields.char(
            'Intrastat Code', size=10, required=True, readonly=True),
        # Field 14: Weight (10 variable 99)
        'weight': fields.char(
            'Weight', size=10, states={'done': [('readonly', True)]}),
        # Field 15: Qty (10 variable 99)
        'quantity': fields.char(
            'Quantity', size=10, states={'done': [('readonly', True)]}),
        # Field 16: Factuurwaarde (10 variable 99)
        'amount_company_currency': fields.integer(
            'Declared value', required=True,
            states={'done': [('readonly', True)]}),
        # Field 17: Externe informatie (13 variable XX)
        'extnr': fields.char(
            'Source reference', size=13, required=True,
            states={'done': [('readonly', True)]}),
        # Field 18: Muntcode (3 fixed XX) (taken from header 'currency_id')
        # Field 19: Incoterm (3 fixed XX)
        'incoterm': fields.related(
            'incoterm_id', 'code', type='char', size='3',
            string='Incoterm Code', readonly=True),
        # Field 20: Gewest (1 fixed XX)
        'region': fields.selection([
            (1, '1. Flemish Region'),
            (2, '2. Walloon Region'),
            (3, '3. Brussels-Capital Region'),
            ], string='Gewest',
            states={'done': [('readonly', True)]}),
    }

    def onchange_country(self, cr, uid, ids, country_id, context=None):
        res = {'value': {}}
        if country_id:
            country = self.pool.get('res.country').browse(
                cr, uid, country_id, context=context)
            res['value'].update({
                'country_id': country.id,
                'country_code': country.code,
            })
        return res

    def onchange_product(self, cr, uid, ids, product_id, qty, context=None):
        res = {'value': {}}
        if product_id:
            product = self.pool.get('product.product').browse(
                cr, uid, product_id, context=context)
            res['value'].update({
                'intrastat_id': product.intrastat_id.id,
                'intrastat_code': product.intrastat_id.intrastat_code,
            })
            if qty:
                res['value'].update({
                    'weight': str(int(round(int(qty) * product.weight_net))),
                })
        return res

    def onchange_qty(self, cr, uid, ids, product_id, qty, context=None):
        res = {'value': {}}
        if product_id and qty:
            product = self.pool.get('product.product').browse(
                cr, uid, product_id, context=context)
            res['value'].update({
                'weight': str(int(round(int(qty) * product.weight_net))),
            })
        return res
