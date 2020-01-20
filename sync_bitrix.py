#!usr/bin/python
import requests
import json
import csv
from collections import defaultdict

auth      = "-------a8"; ### configured on bitrix webhook inbound
user_auth = "---------6fl"; ### configured on bitrix webhook inbound

next      = 1
id_list   = ""

csv_body   = [['companyid','name','staahid']]
def new_decorator(func):
	def wrap_func():
		return func()
	return wrap_func
@new_decorator	
def get_bitrix_property():
	"""
	this function gets all closed won bitrix deals and from that, it gets company names
	and store in csv file
	"""
	while next:
		
		# r = requests.Request('GET',"https://intranet.staah.net/rest/5/"+auth+"/"+method+"?"+id_list)
		# prepared = r.prepare()
		method    = "crm.deal.list"
		response  = requests.get(url="https://intranet.staah.net/rest/5/"+auth+"/"+method+"?FILTER[STAGE_ID]=WON"+id_list)
		print("https://intranet.staah.net/rest/5/"+auth+"/"+method+"?"+id_list)
		json_obj = response.json()
		companies = ""
		try:
			companies= json_obj['result']
		except:
			print(json_obj)
			print(id_list)
			continue
		
		if 'next' in json_obj:
			next = json_obj['next']
		else:
			next = ''
		if next:
			id_list = "&FILTER[>ID]="+companies[len(companies)-1]['ID']
		else:
			id_list = ''
		print('next '+str(next))
		print('total : '+str(json_obj['total']))
		
		
		for ind, company in enumerate(companies):
				
			method    = 'crm.company.get'
			companyid = int(company['COMPANY_ID'])
			if companyid > 0:
				print(str(company['COMPANY_ID']) )
				try:
					comp_detail  = requests.get(url="https://intranet.staah.net/rest/5/"+auth+"/"+method+"?id="+str(companyid))
					comp_json = comp_detail.json()
					company_val = comp_json['result']
				except:
					raise
				
				csv_body.append([companyid,company_val['TITLE'],company_val['UF_CRM_1549917162695']])
			
	if csv_body:
		try:
			with open("bitrix.csv","w") as bitrix_csv:
				writer = csv.writer(bitrix_csv)
				writer.writerows(csv_body)
		except:
			raise

def get_csv_data():
	csv_content = ""
	bitrix_dict = defaultdict(lambda:defaultdict())
	try:
		with open("bitrix.csv","r") as bitrix_csv:
			csv_content = csv.reader(bitrix_csv,delimiter=',')
			for row in csv_content:
				# print (row)
				if row[1] and row[1] != 'name' : 
					bitrix_dict[row[1]]['bitrix_id'] = row[0]
					bitrix_dict[row[1]]['staahid'] = row[2]
	except:
		raise
	return bitrix_dict
	
@new_decorator
def get_staah_props():
	"""
	this function gets all staah properties and compare with bitrix properties by their name
	and create a set of common properties
	"""
	
	moteldata = ""
	try:
		with open("motel_data.json","r",encoding='utf-8') as f:
			data = f.read()
			moteldata = json.loads(data)
	except:
		raise
	
	bitrix_prop = list()
	bitrix_dict = get_csv_data()
	
	for x, det in bitrix_dict.items():
		bitrix_prop.append(x)
	
	bitrix_prop = set(bitrix_prop)
	
	motelnames = list()
	exist_motel = defaultdict()
	if moteldata:
		
		for motelid, det in moteldata.items():
			motelnames.append(det['MotelName'])
			exist_motel[det['MotelName']] = motelid
		# print(motenames)
	
	motelnames = set(motelnames)
	common_prop = set()
	if not ( bitrix_prop == None or motelnames == None ):
		common_prop = motelnames & bitrix_prop
		
	return common_prop, exist_motel
	

def bitrix_without_staahid(common_prop,exist_motel):
	
	bitrix_dict = get_csv_data()
	final_data = defaultdict()
	for props in common_prop:
		if props in bitrix_dict.keys() and bitrix_dict[props]['staahid'] == '':
			final_data[bitrix_dict[props]['bitrix_id']] = exist_motel[props]
	
	for bitrixid, staahid in final_data.items():
		print(bitrixid + ' - ' +staahid)
		# method     = "crm.company.update";
		# filters    = "ID="+bitrixid+"&FIELDS[UF_CRM_1549917162695]="+staahid;
		# comp_detail  = requests.get(url="https://intranet.staah.net/rest/5/"+auth+"/"+method+"?id="+str(companyid))
		# success_update = from_json($upload_staahid)->{result};

common_prop, exist_motel = get_staah_props()
bitrix_without_staahid(common_prop, exist_motel)
