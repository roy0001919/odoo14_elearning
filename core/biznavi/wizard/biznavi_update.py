from openerp import fields, models, api
from subprocess import Popen, PIPE
from openerp.tools.translate import _

class biznavi_update(models.TransientModel):
    _name = 'biznavi.update'
    _description = 'Update BizNavi'
    title = fields.Char(string="Title", size=100, readonly=True)
    message = fields.Text(string="Message", readonly=True)
    updatable = fields.Boolean(string="Updatable", readonly=True)
    _req_name = 'title'

    @api.multi
    def act_ok(self):
        context = dict(self._context or {})
        # git_pull = Popen(['git','pull', '|', 'grep', '"files changed"'], stdout=PIPE).communicate()[0]
        # print git_pull
        # Popen(['python','-m', 'compileall', '.'])
        return {'type': 'ir.actions.act_window_close'}
