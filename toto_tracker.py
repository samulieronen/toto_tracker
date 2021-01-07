import requests
import json
import sys
import pickle

class bcolors:
	ENDC = '\033[0m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'


def compare(data, ref_data):
	new = []
	ref = []
	for item in data:
		new.append(item["percentage"])
	for ref_item in ref_data:
		ref.append(ref_item["percentage"])
	index = 0
	for i in data:
		print(i)
		value = new[index] - ref[index]
		increase = (new[index] - ref[index])
		perc_value = increase / ref[index] * 100
		if perc_value > 20:
			print(bcolors.OKGREEN + "Value change: " + str(value) + " : Percentage change: " + str(perc_value) + "\n" + bcolors.ENDC)
		elif perc_value < -20:
			print(bcolors.WARNING + "Value change: " + str(value) + " : Percentage change: " + str(perc_value) + "\n" + bcolors.ENDC)
		else:
			print("Value change: " + str(value) + " : Percentage change: " + str(perc_value) + "\n")
		index += 1

def validate_creds(usr, pwd, email):
	if len(usr) == 0:
		print(bcolors.FAIL + "ERROR:\n" + bcolors.ENDC + "\tPlease add your Veikkaus account username to the credentials file.\n")
		sys.exit()
	if len(pwd) == 0:
		print(bcolors.FAIL + "ERROR:\n" + bcolors.ENDC + "\tPlease add your Veikkaus account password to the credentials file.\n")
		sys.exit()
	if len(email) == 0:
		print(bcolors.WARNING + "Remember to add your email address to the credentials file.\n" + bcolors.ENDC)
	return usr, pwd, email

def read_credentials():
	with open("credentials") as file:
		text = file.readlines()
		usr = text[1]
		usr = usr[:-1]
		pwd = text[3]
		pwd = pwd[:-1]
		email = text[5]
		email = email[:-1]
	validate_creds(usr, pwd, email)
	return usr, pwd, email

def url(path):
	return "https://www.veikkaus.fi/" + path

headers = {
	"Content-type":"application/json",
	"Accept":"application/json",
	"X-ESA-API-Key":"ROBOT"
	}

def login(usr, pwd):
	sesh = requests.Session()
	login_req = {"type":"STANDARD_LOGIN","login":usr,"password":pwd}
	r = sesh.post(url("api/bff/v1/sessions"), data = json.dumps(login_req), headers = headers)
	if r.status_code == 200:
		print("Login successful")
		return sesh
	else:
		print("Login failed: Status code: " + str(r.status_code))
		sys.exit()

def main():
	usr, pwd, email = read_credentials()
	#sys.exit()
	sesh = login(usr, pwd)
	#res = sesh.get(url("/api/toto-info/v1/cards/date/2021-01-07"))
	res = sesh.get(url("/api/toto-info/v1/pool/7758309/odds"))
	if res.status_code == 200:
		j = res.json()
	else:
		print("Data fetch unsuccessful. Status code: " + str(res.status_code))
	try:
		ref = pickle.load(open("ref.p", "rb"))
		compare(j["odds"], ref)
	except IOError:
		with open("ref.p", "wb") as file:
			pickle.dump(j["odds"], file)
			print("No previous reference data.\nFresh data saved as reference data.")
	if sesh:
		sesh.close()
		print("\nSession closed successfully")
	else:
		print("\nError: No session object!")

main()

