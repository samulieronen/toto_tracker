import requests
import json
import sys
import os
import pickle

class bcolors:
	ENDC = '\033[0m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'

class triggers:
	RISE = 20
	LOW = -15

class bet:
	types = ["T54","T64", "T65", "T75", "T76", "T86", "T87"]

def compare(data, ref_data):
	new = []
	ref = []
	try:
		for item in data:
			item["percentage"] /= 100
			new.append(item["percentage"])
		for ref_item in ref_data:
			ref_item["percentage"] /= 100
			ref.append(ref_item["percentage"])
		index = 0
		printed = 0
		legnb = 0
		for i in data:
			increase = (new[index] - ref[index])
			perc_value = increase / ref[index] * 100
			if perc_value > triggers.RISE or perc_value < triggers.LOW:
				if i["legNumber"] is not legnb:
					legnb = i["legNumber"]
					print("\nLEG {legnb}\n\n".format(legnb = str(legnb)))
				print("Leg: {leggnb} --- Race: {racenb} --- Runner Number: {runnb} --- RaceID: {raceid}".format(leggnb = str(i["legNumber"]), racenb = str(i["raceNumber"]), runnb = str(i["runnerNumber"]), raceid = str(i["raceId"])))
				if perc_value > triggers.RISE:
					print(bcolors.OKGREEN + "RISING!\nRef Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value) + bcolors.ENDC)
				elif perc_value < triggers.LOW:
					print(bcolors.WARNING + "FALLING!\nRef Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value) + bcolors.ENDC)
				else:
					print("Ref Value: {reference}\nNew Value: {fresh}\nPercentage change: {percentage:.2f}%\n".format(reference = ref[index], fresh = new[index], percentage = perc_value))
				printed += 1
			index += 1
		if printed == 0:
			print("No useful data right now. Maybe try later again?")
	except KeyError:
		print("Data cannot be used in comparison. No percentages in data.")
		return

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
	return "https://www.veikkaus.fi" + path

headers = {
	"Content-type":"application/json",
	"Accept":"application/json",
	"X-ESA-API-Key":"ROBOT"
	}

def login(usr, pwd):
	sesh = requests.Session()
	login_req = {"type":"STANDARD_LOGIN","login":usr,"password":pwd}
	r = sesh.post(url("/api/bff/v1/sessions"), data = json.dumps(login_req), headers = headers)
	if r.status_code == 200:
		print("Login successful.")
		return sesh
	else:
		print("Login failed with status code: " + str(r.status_code))
		sesh.close()
		sys.exit()

def check_args(args=[]):
	if len(args) < 1:
		print("No args. Exiting...") # Print usage!!
		sys.exit()
	elif args[0] == "-r" or args[0] == "--races":
		return True
	elif args[0] == "-id":
		if len(args) == 1:
			print("No race ID specified.\nUse '-r' or '--races' to fetch and view available races.")
		return False
	else:
		print("Invalid arguments. Exiting...\n")
		sys.exit()

def print_races(item):
	id = item["cardId"]
	name = item["trackName"]
	country = item["country"]
	cancelled = item["cancelled"]
	racenumber = item["currentRaceNumber"]
	try:
		toto_pools = item["totoPools"]
	except KeyError:
		toto_pools = None
	print(f"\nFound a race with racenumber {racenumber} in {name},{country} with Card ID: {bcolors.OKGREEN}{id}{bcolors.ENDC}")
	if toto_pools is not None:
		pools = "Toto Pools: "
		for i in toto_pools:
			pools += "TOTO "
			pools += i[1:]
			pools += ", "
		print(pools[:-2])
	if cancelled is not False:
		print(f"{bcolors.FAIL}WARNING:{bcolors.ENDC} This race has been cancelled!")
	

def fetch_races(sesh):
	res = sesh.get(url("/api/toto-info/v1/cards/date/today"))
	if res.status_code == 200:
		j = res.json()
		for i in j["collection"]:
			print_races(i)
		print("\n")
		sesh.close()
		sys.exit()
	else:
		print(bcolors.FAIL + "ERROR:\n" + bcolors.ENDC + "\tData fetch unsuccessful with status code: " + str(res.status_code))
		sesh.close()
		print("Session closed successfully.")
		sys.exit()

def fetch_pools(sesh, race_id):
	pools = []
	res = sesh.get(url(f"/api/toto-info/v1/card/{race_id}/pools"))
	if res.status_code == 200:
		j = res.json()
		for i in j["collection"]:
			bet_type = i["poolType"]
			if bet_type in bet.types:
				pools.append(i["poolId"])
	return pools

def handle_data(sesh, pool_id):
	res = sesh.get(url(f"/api/toto-info/v1/pool/{pool_id}/odds"))
	if res.status_code == 200:
		j = res.json()
	else:
		print(bcolors.FAIL + "ERROR:\n" + bcolors.ENDC + "\tData fetch unsuccessful with status code: " + str(res.status_code))
		sesh.close()
		print("Session closed successfully.")
		sys.exit()
	try:
		ref = pickle.load(open(f"ref_{pool_id}.p", "rb"))
		compare(j["odds"], ref)
	except IOError:
		os.system(f"touch ref_{pool_id}.p")
		with open(f"ref_{pool_id}.p", "wb") as file:
			pickle.dump(j["odds"], file)
			print(f"No previous reference data for pool {pool_id}.\nFresh data saved as reference data.")

def main():
	try:
		usr, pwd, email = read_credentials()
		mod = check_args(sys.argv[1:])
		sesh = login(usr, pwd)
		if mod == True:
			fetch_races(sesh)
			sys.exit()
		race_id = sys.argv[2]
		pools = fetch_pools(sesh, race_id)
		for id in pools:
			handle_data(sesh, id)
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

