# -*- coding: utf-8 -*-

import xmlrpclib

srv = 'https://xikoubridge.cenoq.com'

common = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % srv)

uid = common.authenticate('xikoubridge', 'admin', 'cenoq28004668', {})
print uid
