import cStringIO
import threading

import time

from odoo.modules import module

from odoo import _
from odoo import fields, models, api
import odoo
import logging
import os

_logger = logging.getLogger(__name__)


class TranslationWritebackWizard(models.TransientModel):
    _name = 'biznavi.translation_writeback_wizard'
    _description = 'Translation Writeback'

    modules = fields.Many2many('ir.module.module', string="Modules")
    rewrite_pot = fields.Boolean(String="Rewrite POT")
    process_base = fields.Boolean(String="Process base module")

    @api.multi
    def act_exec_writeback(self):
        modules = self.modules
        if len(modules) == 0:
            modules = self.env['ir.module.module'].search([('state', '=', 'installed')])
        dbname = self.env.cr.dbname
        # thread_arr = []
        for m in modules:
            if self.process_base or m.name != 'base':
                self.do_writeback(m, dbname)
            # t = threading.Thread(target=self.do_writeback, name='Thd_'+m.name, args=(m, dbname))
            # t.start()
            # thread_arr.append(t)

        # while len(thread_arr) > 0:
        # 	time.sleep(1)
        # 	for t in thread_arr:
        # 		if not t.is_alive():
        # 			thread_arr.remove(t)

        msg = _('Writeback Completed!\n')
        ctx = dict(
            default_message=msg,
        )
        return {
            'name': _('BizNavi Translation Writeback'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'biznavi.update',
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def do_writeback(self, m, dbname):
        i18n_path = os.path.join(module.get_module_path(m.name), 'i18n')
        pot_path = os.path.join(i18n_path, m.name + '.pot')
        lang_path = os.path.join(i18n_path, 'zh_TW.po')
        fix_terms = ""

        if not os.path.exists(i18n_path):
            return fix_terms
        if not os.path.exists(lang_path):
            open(lang_path, 'a').close()
        with open(lang_path, "r+") as buf:
            registry = odoo.modules.registry.RegistryManager.new(dbname)
            with odoo.api.Environment.manage():
                with registry.cursor() as cr:

                    output = cStringIO.StringIO()
                    odoo.tools.trans_export("zh_TW", [m.name], output, "po", cr)
                    contents = output.getvalue()
                    current = buf.read()
                    # contents = buf.read()
                    diff = set(contents.split("\n")).difference(current.split("\n"))
                    writeback = False
                    for line in diff:
                        if "POT-Creation-Date:" not in line and "PO-Revision-Date:" not in line:
                            writeback = True
                            if "msgstr " in line:
                                fix_terms += "%s\n" % line.replace("msgstr ", "")
                    if writeback:
                        # msg += "\n%s: \n%s" % (m.name, fix_terms)
                        buf.seek(0)
                        buf.write(contents)
                        buf.truncate()
                        if self.rewrite_pot:
                            with open(pot_path, "w") as pot:
                                odoo.tools.trans_export(None, [m.name], pot, "po", cr)

                    output.close()

        _logger.info('Translation writebacked: %s ' % m.name)
        return fix_terms
