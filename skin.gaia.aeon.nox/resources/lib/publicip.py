# GAIA

import xbmcgui
import urllib2
import json

publicip = None
publiccountry = None

if publicip == None:
	try:
		result = json.load(urllib2.urlopen('http://ip-api.com/json'))
		publicip = result['query']
		publiccountry = result['country']
	except: pass

if publicip == None:
	try:
		result = json.load(urllib2.urlopen('http://freegeoip.net/json/'))
		publicip = result['ip']
		publiccountry = result['country_name']
	except: pass
	
if publicip == None:
	try:
		result = json.load(urllib2.urlopen('https://tools.keycdn.com/geo.json'))
		publicip = result['data']['geo']['ip']
		publiccountry = result['data']['geo']['country_name']
	except: pass
	
if publicip == None:
	try:
		result = json.load(urllib2.urlopen('http://extreme-ip-lookup.com/json/'))
		publicip = result['query']
		publiccountry = result['country']
	except: pass
	
if publicip == None:
	try: publicip = urllib2.urlopen('http://ip.42.pl/raw').read()
	except: pass

if publicip == None:
	try: publicip = json.loads(urllib2.urlopen('http://httpbin.org/ip'))['origin']
	except: pass
	
if publicip == None:
	try: publicip = json.loads(urllib2.urlopen('https://api.ipify.org/?format=json'))['ip']
	except: pass

if publicip == None: publicip = ''
if publiccountry == None: publiccountry = ''

xbmcgui.Window(10000).setProperty('publicnetwork', '%s %s' % (publicip, publiccountry))
xbmcgui.Window(10000).setProperty('publicnetworkformat', '%s[COLOR grey] %s[/COLOR]' % (publicip, publiccountry))
xbmcgui.Window(10000).setProperty('publicip', publicip)
xbmcgui.Window(10000).setProperty('publiccountry', publiccountry)