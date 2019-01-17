# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate_line_global(cr):

    g_table = 'account_bank_statement_line_global'

    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = '%s' "
        "AND column_name = 'currency_id'"
        % g_table)

    if not cr.fetchone():
        cr.execute("ALTER TABLE %s ADD COLUMN currency_id integer" % g_table)
        cr.execute("COMMENT ON COLUMN %s.currency_id IS 'Currency'" % g_table)

    cr.execute(
        "SELECT DISTINCT(g.id) "
        "FROM account_bank_statement_line l "
        "JOIN %s g "
        "ON l.globalisation_id = g.id"
        % g_table)
    res = cr.fetchall()
    gids = [x[0] for x in res]

    for gid in gids:

        cr.execute(
            "SELECT id FROM account_bank_statement_line "
            "WHERE globalisation_id = %s LIMIT 1" % gid)
        res = cr.fetchone()
        lid = res[0]

        cr.execute(
            "SELECT jc.id AS jc_id, cc.id as cc_id "
            "FROM account_bank_statement_line l "
            "JOIN account_bank_statement s ON l.statement_id = s.id "
            "JOIN account_journal j ON s.journal_id = j.id "
            "JOIN res_company c ON l.company_id = c.id "
            "JOIN res_currency cc ON c.currency_id = cc.id "
            "LEFT OUTER JOIN res_currency jc ON j.currency_id = jc.id "
            "WHERE l.id = %s" % lid)
        res = cr.fetchone()
        cid = res[0] or res[1]

        update = "UPDATE %s SET currency_id = %s " % (g_table, cid)
        update += "WHERE id = %s"

        def update_glob_line(gid):
            cr.execute(update % gid)
            parent_id = gid
            cr.execute(
                "SELECT id FROM account_bank_statement_line_global "
                "WHERE parent_id = '%s'" % parent_id)
            res = cr.fetchall()
            child_ids = [x[0] for x in res]
            for child_id in child_ids:
                update_glob_line(child_id)

        update_glob_line(gid)


def migrate(cr, version):
    if not version:
        return

    migrate_line_global(cr)
