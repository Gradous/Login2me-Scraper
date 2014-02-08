from bs4 import BeautifulSoup
import urllib2
bmn_req = urllib2.Request('http://bugmenot.com/', headers={'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64)'})
try:
	response = urllib2.urlopen(bmn_req)
except urllib2.HTTPError, e:
	print "Error code: ", e.code
	print e.fp.read()
	raise e

html = response.read()
print html
