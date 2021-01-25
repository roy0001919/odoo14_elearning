# -*- encoding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def compose_body(obj, vals):
	msgs = []
	for key in vals:
		field = obj.fields_get()[key]
		if field:
			val = vals[key]
			org_val, new_val = None, None
			if field['type'] in ['char', 'integer', 'date', 'datetime']:
				org_val = obj[key]
				new_val = val
			elif field['type'] == 'boolean':
				org_val = u'☑' if obj[key] else u'☐'
				new_val = u'☑' if val else u'☐'
			elif field['type'] == 'selection' and key != 'state':
				org_val = dict(obj.fields_get()[key]['selection']).get(obj[key])
				new_val = dict(obj.fields_get()[key]['selection']).get(val)
			elif field['type'] == 'many2one' and field['relation'] != 'res.partner':
				org_val = obj[key][obj._rec_name]
				new_val = obj.env[obj.fields_get()[key]['relation']].browse(val)[obj._rec_name]
			elif obj.fields_get()[key]['type'] == 'one2many':
				# org_val = ", ".join([i[i._rec_name] for i in obj[key] if i[i._rec_name]])
				r = []
				rec_name = obj.env[obj.fields_get()[key]['relation']]._rec_name
				for i in val:
					if i[0] == 1:
						rec = dict(i[2]).get(rec_name)
						r.append("* %s" % rec if rec else "")
					elif i[0] == 2:
						rec = obj.env[obj.fields_get()[key]['relation']].browse(i[1])[rec_name]
						r.append("- %s" % rec if rec else "")
					elif i[0] == 0:
						rec = dict(i[2]).get(rec_name)
						r.append("+ %s" % rec if rec else "")
				new_val = ", ".join(r)
			elif obj.fields_get()[key]['type'] == 'many2many':
				org_val = ", ".join([i[i._rec_name] for i in obj[key] if i[i._rec_name]])
				new_val = ", ".join([i[i._rec_name] for i in obj.env[obj.fields_get()[key]['relation']].browse(val[0][2])])
			if new_val != org_val:
				prev = '%s <span class="fa fa-long-arrow-right"/> ' % org_val if org_val else ""
				msgs.append('%s: %s%s' % (obj.fields_get()[key]['string'], prev, new_val))

	if len(msgs) > 0:
		return '<ul class="o_mail_thread_message_tracking"><span><li>%s</span></li></ul>' % ('</span></li><span><li>'.join(msgs))


def translate_body(obj, vals, show_state=False):
	msgs = []
	_logger.info('showstate:%s' % show_state)
	for key in vals:
		field = obj.fields_get()[key]
		if field:
			val = vals[key]
			org_val, new_val = None, None
			if field['type'] in ['char', 'text', 'integer', 'date', 'datetime']:
				org_val = obj[key]
				new_val = val
			elif field['type'] == 'boolean':
				org_val = u'☑' if obj[key] else u'☐'
				new_val = u'☑' if val else u'☐'
			elif field['type'] == 'selection' and (show_state or key != 'state'):
				org_val = dict(obj.fields_get()[key]['selection']).get(obj[key])
				new_val = dict(obj.fields_get()[key]['selection']).get(val)
			elif field['type'] == 'many2one' and field['relation'] != 'res.partner':
				org_val = obj[key][obj._rec_name]
				new_val = obj.env[obj.fields_get()[key]['relation']].browse(val)[obj._rec_name]
			elif obj.fields_get()[key]['type'] == 'one2many':
				# org_val = ", ".join([i[i._rec_name] for i in obj[key] if i[i._rec_name]])
				r = []
				rec_name = obj.env[obj.fields_get()[key]['relation']]._rec_name
				for i in val:
					if i[0] == 1:
						rec = dict(i[2]).get(rec_name)
						r.append("* %s" % rec if rec else "")
					elif i[0] == 2:
						rec = obj.env[obj.fields_get()[key]['relation']].browse(i[1])[rec_name]
						r.append("- %s" % rec if rec else "")
					elif i[0] == 0:
						rec = dict(i[2]).get(rec_name)
						r.append("+ %s" % rec if rec else "")
				new_val = ", ".join(r)
			elif obj.fields_get()[key]['type'] == 'many2many':
				org_val = ", ".join([i[i._rec_name] for i in obj[key] if i[i._rec_name]])
				new_val = ", ".join([i[i._rec_name] for i in obj.env[obj.fields_get()[key]['relation']].browse(val[0][2])])

			if new_val != org_val:
				prev = '%s' % org_val if org_val else ""
				msgs.append('%s: %s -> %s' % (obj.fields_get()[key]['string'], prev, new_val))

	if len(msgs) > 0:
		return '%s' % ('\n'.join(msgs))