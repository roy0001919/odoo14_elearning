# -*- coding: utf-8 -*-
wage = int((151500-1)/500)*500
x_raise = 10
annual = wage * 12
free = (x_raise+1) * 85000
std_raise = 180000
spc_raise = 128000

v1 = annual - (free + std_raise + spc_raise)
print v1

v2 = 0
if v1 <= 520000:
	v2 = round(v1 * 0.05) - 0
elif 520001 <= v1 <= 1170000:
	v2 = round(v1 * 0.12) - 36400
elif 1170001 <= v1 <= 2350000:
	v2 = round(v1 * 0.2) - 130000
elif 2350001 <= v1 <= 4400000:
	v2 = round(v1 * 0.3) - 365000
elif 4400001 <= v1:
	v2 = round(v1 * 0.4) - 805000

v3 = int(v2/12/10) * 10
print v3 if v3 > 2000 else 0

# hi_range = [20008,20100,21000,21900,22800,24000,25200,26400,27600,28800,30300,31800,33300,34800,36300,38200,40100,42000,43900]
# x = 30300
# y = 0
# for i in range(len(hi_range)):
# 	if x > hi_range[i]:
# 		pass
# 	else:
# 		y = hi_range[i]
# 		break
#
# print "Y=[%d]" % y

# if (x_wage < 20008):
#     w_rel_wage = 20008
# elif ( 20009 <= x_wage <= 20100):
# 	w_rel_wage = 20100
# elif ( 20101 <= x_wage <= 21000):
# 	w_rel_wage = 21000
# elif ( 21001 <= x_wage <= 21900):
# 	w_rel_wage = 21900
# elif ( 21901 <= x_wage <= 22800):
# 	w_rel_wage = 22800
# elif ( 22801 <= x_wage <= 24000):
# 	w_rel_wage = 24000
# elif ( 24001 <= x_wage <= 25200):
# 	w_rel_wage = 25200
# elif ( 25201 <= x_wage <= 26400):
# 	w_rel_wage = 26400
# elif ( 26401 <= x_wage <= 27600):
# 	w_rel_wage = 27600
# elif ( 27601 <= x_wage <= 28800):
# 	w_rel_wage = 28800
# elif ( 28801 <= x_wage <= 30300):
# 	w_rel_wage = 30300
# elif ( 30301 <= x_wage <= 31800):
# 	w_rel_wage = 31800
# elif ( 31801 <= x_wage <= 33300):
# 	w_rel_wage = 33300
# elif ( 33301 <= x_wage <= 34800):
# 	w_rel_wage = 34800
# elif ( 34801 <= x_wage <= 36300):
# 	w_rel_wage = 36300
# elif ( 36301 <= x_wage <= 38200):
# 	w_rel_wage = 38200
# elif ( 38201 <= x_wage <= 40100):
# 	w_rel_wage = 40100
# elif ( 40101 <= x_wage <= 42000):
# 	w_rel_wage = 42000
# elif ( 42001 <= x_wage):
# 	w_rel_wage = 43900
# else:
# 	pass


## HI
# x_hi_rate = 0.0491
# x_wage = contract.wage
# x_raise = contract.raise_amount
# if x_raise >= 3:
#     x_raise = 4
# else:
#     x_raise = 1 + x_raise
#
# w_rel_wage = 0
# if (x_wage < 20008):
#     w_rel_wage = 20008
# elif ( 20009 <= x_wage <= 20100):
# 	w_rel_wage = 20100
# elif ( 20101 <= x_wage <= 21000):
# 	w_rel_wage = 21000
# elif ( 21001 <= x_wage <= 21900):
# 	w_rel_wage = 21900
# elif ( 21901 <= x_wage <= 22800):
# 	w_rel_wage = 22800
# elif ( 22801 <= x_wage <= 24000):
# 	w_rel_wage = 24000
# elif ( 24001 <= x_wage <= 25200):
# 	w_rel_wage = 25200
# elif ( 25201 <= x_wage <= 26400):
# 	w_rel_wage = 26400
# elif ( 26401 <= x_wage <= 27600):
# 	w_rel_wage = 27600
# elif ( 27601 <= x_wage <= 28800):
# 	w_rel_wage = 28800
# elif ( 28801 <= x_wage <= 30300):
# 	w_rel_wage = 30300
# elif ( 30301 <= x_wage <= 31800):
# 	w_rel_wage = 31800
# elif ( 31801 <= x_wage <= 33300):
# 	w_rel_wage = 33300
# elif ( 33301 <= x_wage <= 34800):
# 	w_rel_wage = 34800
# elif ( 34801 <= x_wage <= 36300):
# 	w_rel_wage = 36300
# elif ( 36301 <= x_wage <= 38200):
# 	w_rel_wage = 38200
# elif ( 38201 <= x_wage <= 40100):
# 	w_rel_wage = 40100
# elif ( 40101 <= x_wage <= 42000):
# 	w_rel_wage = 42000
# elif ( 42001 <= x_wage <= 43900):
# 	w_rel_wage = 43900
# elif ( 43901 <= x_wage <= 45800):
# 	w_rel_wage = 45800
# elif ( 45801 <= x_wage <= 48200):
# 	w_rel_wage = 48200
# elif ( 48201 <= x_wage <= 50600):
# 	w_rel_wage = 50600
# elif ( 50601 <= x_wage <= 53000):
# 	w_rel_wage = 53000
# elif ( 53001 <= x_wage <= 55400):
# 	w_rel_wage = 55400
# elif ( 55401<= x_wage <= 57800):
# 	w_rel_wage = 57800
# elif ( 57801<= x_wage <= 60800):
# 	w_rel_wage = 60800
# elif ( 60801<= x_wage <= 63800):
# 	w_rel_wage = 63800
# elif ( 63801<= x_wage <= 66800):
# 	w_rel_wage = 66800
# elif ( 66801<= x_wage <= 69800):
# 	w_rel_wage = 69800
# elif ( 69801 <= x_wage <= 72800):
# 	w_rel_wage = 72800
# elif ( 72801 <= x_wage <= 76500):
# 	w_rel_wage = 76500
# elif ( 76501<= x_wage <= 80200):
# 	w_rel_wage = 80200
# elif ( 80201 <= x_wage <= 83900):
# 	w_rel_wage = 83900
# elif ( 83901<= x_wage <= 87600):
# 	w_rel_wage = 87600
# elif ( 87601<= x_wage <= 92100):
# 	w_rel_wage = 92100
# elif ( 92101<= x_wage <= 96600):
# 	w_rel_wage = 96600
# elif ( 96601 <= x_wage <= 101100):
# 	w_rel_wage = 101100
# elif ( 101101 <= x_wage <= 105600):
# 	w_rel_wage = 105600
# elif ( 105601 <= x_wage <= 110100):
# 	w_rel_wage = 110100
# elif ( 110101 <= x_wage <= 115500):
# 	w_rel_wage = 115500
# elif ( 115501 <= x_wage <= 120900):
# 	w_rel_wage = 120900
# elif ( 120901 <= x_wage <= 126300):
# 	w_rel_wage = 126300
# elif ( 126301 <= x_wage <= 131700):
# 	w_rel_wage = 131700
# elif ( 1317101 <= x_wage <= 137100):
# 	w_rel_wage = 137100
# elif ( 137101 <= x_wage <= 142500):
# 	w_rel_wage = 142500
# elif ( 142501 <= x_wage <= 147900):
# 	w_rel_wage = 147900
# elif ( 147901 <= x_wage <= 150000):
# 	w_rel_wage = 150000
# elif ( 150001 <= x_wage <= 156400):
# 	w_rel_wage = 156400
# elif ( 156401 <= x_wage <= 162800):
# 	w_rel_wage = 162800
# elif ( 162801 <= x_wage <= 169200):
# 	w_rel_wage = 169200
# elif ( 169201 <= x_wage <= 175600):
# 	w_rel_wage = 175600
# elif ( 175601 <= x_wage ):
#         w_rel_wage = 18200
# else:
# 	pass
#
# x_rel_wage = w_rel_wage
#
# result = -1 * round( x_rel_wage * x_hi_rate * 0.3) * (x_raise)