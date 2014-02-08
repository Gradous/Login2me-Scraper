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

	bmn_soup = BeautifulSoup(bugmenot_response.read())
	accounts = bmn_soup.findAll(class_="account")
	names = BeautifulSoup(str(accounts)).findAll('kbd')
	print names

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

