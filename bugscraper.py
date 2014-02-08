from bs4 import BeautifulSoup
import urllib2

"""
Globals
"""


def scrape(url):
	# Spoof our user agent since BMN doesn't like bots
	bugmenot_req = urllib2.Request('http://bugmenot.com/view/' + url,
		headers={'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64)'})
	try:
		bugmenot_response = urllib2.urlopen(bugmenot_req)
	except urllib2.HTTPError, e:
		print "Error code: ", e.code
		print e.fp.read()
		raise e

	bmn_soup = BeautifulSoup(bugmenot_response.read()).findAll(class_="account")

	""" 
	The soup will be empty if the page has no accounts or falls into the "bad"
	category (paywalled, commmunity, etc.)
	"""
	if not bmn_soup:
		print "No results for:", url
		return

	# Buckets for parsing
	usernames = []
	passwords = []
	rates = []

	for account in bmn_soup:
		# First, parse the accounts for usernames and passwords
		counter = 0 
		for userpass in BeautifulSoup(str(account)).findAll('kbd'):
			if counter == 0: # we have a username
				usernames.append(userpass.contents)
			elif counter == 1: # we have a password
				passwords.append(userpass.contents)
			else: # we have a comment, ignore it and reset counter
				counter = 0
			counter += 1
		# Next, parse for the success rates
		for success in BeautifulSoup(str(account)).findAll(class_='success_rate'):
			rates.append(success.contents)

	print zip(usernames, passwords, rates)


if __name__ == "__main__":
	scrape("xe.gr")
	"""
	with open('alexa_top_1m.csv') as alexa_list:
		for site in alexa_list:
			print site.rsplit(',')
			# print site.rsplit(',')[1].strip()
			if int(site.rsplit(',')[0]) >= 1000:
				break
	"""

