# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET

xmlStr = """
<ServerResponse xmlns="http://schemas.datacontract.org/2004/07/SinoPacWebAPI.Contract" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
  <OrderNO>S18000037</OrderNO>
  <ShopNO>AB0427</ShopNO>
  <KeyNum>2</KeyNum>
  <TSNO>AB04270000008</TSNO>
  <PayType>A</PayType>
  <PayNO>99936820015272</PayNO>
  <Amount>324000</Amount>
  <Status>S</Status>
  <Description>S00000</Description>
  <Param1></Param1>
  <Param2></Param2>
  <Param3></Param3>
</ServerResponse>
"""

root = ET.fromstring(xmlStr)

for child in root:

    if child.tag.find('TSNO') > 0:
        txNo = child.text
        print txNo

    if child.tag.find('PayNO') > 0:
        payNo = child.text
        print payNo

str1 = '20180101'
str2 = '20180102'

print str1 > str2
print str1 < str2
    # if child.tag == 'TSNO':
    #     txNo = child.text
    #
    # if child.tag == 'PayNO':
    #     payNo = child.text

