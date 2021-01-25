# -*- encoding: utf-8 -*-

public_days_array = []
year = '2016'
line1 = True

with open('2016.txt') as f:
	public_days_array = f.readlines()

outputfile = open('2016_out.csv', 'w')
outputfile.write('year,line_ids/adj_working_day,line_ids/date,line_ids/name\n')
adj_wd = False
for pd in public_days_array:
	if len(pd.decode('utf-8')) > 11:
		print('0/2: %s - %s' % (pd[12:len(pd)-1], pd[11:12]))
		if pd[11:12] == '2':
			adj_wd = 'False'
		else:
			adj_wd = 'True'
		if line1:
			# print('%s,%s-%s-%s,%s' % (year, pd[:4], pd[4:6], pd[6:8], pd[12:]))
			tmp_str = '%s,%s,%s-%s-%s,%s' % (year, adj_wd, pd[:4], pd[4:6], pd[6:8], pd[12:])
			line1 = False
			outputfile.write(tmp_str)
		else:
			# print(',%s-%s-%s,%s' % (pd[:4], pd[4:6], pd[6:8], pd[12:]))
			tmp_str = ',%s,%s-%s-%s,%s' % (adj_wd, pd[:4], pd[4:6], pd[6:8], pd[12:])
			outputfile.write(tmp_str)

outputfile.close()