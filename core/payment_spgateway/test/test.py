# -*- coding: utf-8 -*-
import urllib
import hashlib

sp_hash_key = '1A3S21DAS3D1AS65D1'
sp_hash_iv = '1AS56D1AS24D'

to_sign = {}
to_sign.update(
{
	'MerchantID': '123456',
    'TimeStamp': '1403243286',
    'MerchantOrderNo': '20140901001',
    'Version': '1.1',
    'Amt': '200',
})

sorted_to_sign = sorted(to_sign.iteritems())
print 'sorted: %s' % sorted_to_sign
urlencodestr = urllib.urlencode(sorted_to_sign)
print 'encoded: %s' % urlencodestr
finalstr = 'HashKey=%s&%s&HashIV=%s' % (sp_hash_key, urlencodestr, sp_hash_iv)
print 'finalstr: %s' % finalstr
hashstr = hashlib.sha256(finalstr).hexdigest().upper()
print 'hashstr: %s' % hashstr