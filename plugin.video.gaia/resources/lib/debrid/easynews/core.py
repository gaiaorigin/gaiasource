# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib.debrid import base
from resources.lib.extensions import convert
from resources.lib.extensions import cache
from resources.lib.extensions import tools

class Core(base.Core):

	Id = 'easynews'
	Name = 'EasyNews'
	Abbreviation = 'E'

	Cookie = 'chickenlicker=%s%%3A%s'

	LinkLogin = 'https://account.easynews.com/index.php'
	LinkAccount = 'https://account.easynews.com/editinfo.php'
	LinkUsage = 'https://account.easynews.com/usageview.php'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name)

		self.mResult = None
		self.mSuccess = False
		self.mError = None
		self.mCookie = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		import urllib
		from resources.lib.modules import client

		self.mResult = None
		self.mSuccess = True
		self.mError = None

		if not httpTimeout: httpTimeout = 30

		def login():
			data = urllib.urlencode({'username': self.accountUsername(), 'password': self.accountPassword(), 'submit': 'submit'})
			self.mCookie = client.request(Core.LinkLogin, post = data, output = 'cookie', close = False)

		try:
			if parameters: parameters = urllib.urlencode(parameters)

			if self.mCookie == None: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			if 'value="Login"' in self.mResult: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			self.mSuccess = self.mCookie and not 'value="Login"' in self.mResult
			if not self.mSuccess: self.mError = 'Login Error'
		except:
			toosl.Logger.error()
			self.mSuccess = False
			self.mError = 'Unknown Error'
		return self.mResult

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.easynews', raw = True)
		if open: tools.System.openLink(link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('link.easynews.vpn', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.easynews.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountPassword() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.easynews.user') if self.accountEnabled() else ''

	def accountPassword(self):
		return tools.Settings.getString('accounts.debrid.easynews.pass') if self.accountEnabled() else ''

	def accountCookie(self):
		return Core.Cookie % (self.accountUsername(), self.accountPassword())

	def accountVerify(self):
		return not self.account(cached = False, minimal = True) == None

	def account(self, cached = True, minimal = False):
		account = None
		try:
			if self.accountValid():
				import datetime
				from resources.lib.externals.beautifulsoup import BeautifulSoup

				if cached: accountHtml = cache.Cache().cacheShort(self._request, Core.LinkAccount)
				else: accountHtml = cache.Cache().cacheClear(self._request, Core.LinkAccount)

				if accountHtml == None or accountHtml == '': raise Exception()

				accountHtml = BeautifulSoup(accountHtml)
				accountHtml = accountHtml.find_all('form', id = 'accountForm')[0]
				accountHtml = accountHtml.find_all('table', recursive = False)[0]
				accountHtml = accountHtml.find_all('tr', recursive = False)

				accountUsername = accountHtml[0].find_all('td', recursive = False)[1].getText()
				accountType = accountHtml[1].find_all('td', recursive = False)[2].getText()
				accountStatus = accountHtml[3].find_all('td', recursive = False)[2].getText()

				accountExpiration = accountHtml[2].find_all('td', recursive = False)[2].getText()
				accountTimestamp = convert.ConverterTime(accountExpiration, format = convert.ConverterTime.FormatDate).timestamp()
				accountExpiration = datetime.datetime.fromtimestamp(accountTimestamp)

				account = {
					'user' : accountUsername,
					'type' : accountType,
					'status' : accountStatus,
			 		'expiration' : {
						'timestamp' : accountTimestamp,
						'date' : accountExpiration.strftime('%Y-%m-%d'),
						'remaining' : (accountExpiration - datetime.datetime.today()).days,
					}
				}

				if not minimal:
					if cached: usageHtml = cache.Cache().cacheShort(self._request, Core.LinkUsage)
					else: usageHtml = cache.Cache().cacheClear(self._request, Core.LinkUsage)

					if usageHtml == None or usageHtml == '': raise Exception()

					usageHtml = BeautifulSoup(usageHtml)
					usageHtml = usageHtml.find_all('div', class_ = 'table-responsive')[0]
					usageHtml = usageHtml.find_all('table', recursive = False)[0]
					usageHtml = usageHtml.find_all('tr', recursive = False)

					account['usageTotal'] = usageHtml[0].find_all('td', recursive = False)[1].getText()
					account['remaining'] = usageHtml[1].find_all('td', recursive = False)[2].getText()
					usageLoyaltyTime = usageHtml[2].find_all('td', recursive = False)[2].getText()

					usageLoyaltyTime = usageLoyaltyTime[0 : usageLoyaltyTime.find(' ')].strip()
					account['loyaltyDate'] = usageLoyaltyTime
		except:
			pass
		return account
