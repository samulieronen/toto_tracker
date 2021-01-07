import requests
import json
import sys
import pickle

class bcolors:
	ENDC = '\033[0m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'

class triggers:
	RISE = 30
	LOW = -15

def compare(data, ref_data):
	new = []
	ref = []
	for item in data:
		item["percentage"] /= 100
		new.append(item["percentage"])
	for ref_item in ref_data:
		ref_item["percentage"] /= 100
		ref.append(ref_item["percentage"])
	index = 0
	legnb = 0
	for i in data:
		if i["legNumber"] is not legnb:
			legnb = i["legNumber"]
			print("\nLEG {legnb}\n\n".format(legnb = str(legnb)))
		increase = (new[index] - ref[index])
		perc_value = increase / ref[index] * 100
		print("Leg: {leggnb} --- Race: {racenb} --- Runner Number: {runnb} --- RaceID: {raceid}".format(leggnb = str(i["legNumber"]), racenb = str(i["raceNumber"]), runnb = str(i["runnerNumber"]), raceid = str(i["raceId"])))
		if perc_value > triggers.RISE:
			print(bcolors.OKGREEN + "RISING!\nRef Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value) + bcolors.ENDC)
		elif perc_value < triggers.LOW:
			print(bcolors.WARNING + "FALLING!\nRef Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value) + bcolors.ENDC)
		else:
			print("Ref Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value))
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
		print("Login successful.")
		return sesh
	else:
		print("Login failed with status code: " + str(r.status_code))
		sesh.close()
		sys.exit()

def main():
	try:
		usr, pwd, email = read_credentials()
		sesh = login(usr, pwd)
		res = sesh.get(url("/api/toto-info/v1/pool/7758309/odds"))
		if res.status_code == 200:
			j = res.json()
		else:
			print(bcolors.FAIL + "ERROR:\n" + bcolors.ENDC + "\tData fetch unsuccessful with status code: " + str(res.status_code))
			sesh.close()
			print("Session closed successfully.")
			sys.exit()
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
			sys.exit()
	except KeyboardInterrupt:
		if sesh is not None:
			sesh.close()

main()

