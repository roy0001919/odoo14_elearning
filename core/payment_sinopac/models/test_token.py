# coding: utf-8
from hashlib import sha256
import ssl
import urllib2
import datetime
import xml.etree.cElementTree as ET

# ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

datetime.datetime.now()

def _sinopac_generate_merchant_sig_sha256(values):
    print('data: %s' % values)
    shasign = sha256(values).hexdigest()
    print('shasign: %s' % shasign)
    return shasign

html2 = '''
<html>#015#012
<body>#015#012
<form name=fm method=post action=https://khskywalkpark.com/payment/sinopac/inquery>#015#012
lastPan4:<input type=hidden name=lastPan4 value=7212><BR/>
txstatus:<input type=hidden name=txstatus value=0><BR/>
authCode:<input type=hidden name=authCode value=343563><BR/>
purchAmt:<input type=hidden name=purchAmt value=660><BR/>
txerrcode:<input type=hidden name=txerrcode value=00><BR/>
merID:<input type=hidden name=merID value=28004668><BR/>
xid:<input type=hidden name=xid value=O-OBJECT-20180530135214.262-2121><BR/>
rescode:<input type=hidden name=rescode value=0><BR/>
lidm:<input type=hidden name=lidm value=S18049694><BR/>
MerchantID:<input type=hidden name=MerchantID value=807280046688001><BR/>
amtRefundTotal:<input type=hidden name=amtRefundTotal value=0><BR/>
TerminalID:<input type=hidden name=TerminalID value=80010808><BR/>
txstate:<input type=hidden name=txstate value=1><BR/>#015#012
<script Language=JavaScript>this.document.fm.submit();</script>#015#012
</form>
</body>
</html>
'''
html = '''
<html>#015#012<body>#015#012
<form name=fm method=post action=https://khskywalkpark.com/payment/sinopac/inquery>#015#012
MerchantID:<input type=hidden name=MerchantID value=807280046688001><BR/>
purchAmt:<input type=hidden name=purchAmt value=1100><BR/>
merID:<input type=hidden name=merID value=28004668><BR/>
TerminalID:<input type=hidden name=TerminalID value=80010808><BR/>
xid:<input type=hidden name=xid value=><BR/>
rescode:<input type=hidden name=rescode value=10><BR/>
lidm:<input type=hidden name=lidm value=S18049693><BR/>#015#012
<script Language=JavaScript>this.document.fm.submit();</script>#015#012</form></body></html>
'''

if html.find("name=txstatus value=0>") > 0 and html.find("name=authCode") > 0 and html.find("name=xid value=>") < 0:
    print 'True'
else:
    print 'False'
# val = '20131024T009&200&1qaz2wsx3edc4rfv&950876543219001&90010001&20131024141500'
# token = _sinopac_generate_merchant_sig_sha256(val)
# compStr = '935D2F84CBEC53716F5EB643FCE88C4DB6807372061821373F98AA0A38A10C5F'
# print '1.compare result : %s' % (token.upper() == compStr)
#
# val = '0&20131024T009&1qaz2wsx3edc4rfv&887693&20131024141600&950876543219001&90010001'
# token = _sinopac_generate_merchant_sig_sha256(val)
# compStr = '428729487F8BE0329DD08AB8CDFCE677BEA16B04298EA46F1EBFA4C1EA4146C1'
# print '2.compare result : %s' % (token.upper() == compStr)
#
# val = '8&30&20131024T009&1qaz2wsx3edc4rfv&20131024141600&950876543219001&90010001'
# token = _sinopac_generate_merchant_sig_sha256(val)
# compStr = '5B0FB1319A9ADADFB274199B6FEF815F3B3252EC86DE06A974B03499980A1CBB'
# print '3.compare result : %s' % (token.upper() == compStr)

# ret_lidm = 'S18000010'
# strXIdx = ret_lidm.find('x')
# strXIdx = ret_lidm.find('x')
# print strXIdx
# print ret_lidm[:strXIdx]
#
# parse_ret_lidm = lambda ret_lidm: ret_lidm[:ret_lidm.find('x')] if ret_lidm.find('x')!=-1 else ret_lidm
# print parse_ret_lidm(ret_lidm)
