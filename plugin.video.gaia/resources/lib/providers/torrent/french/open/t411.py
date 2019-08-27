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

import re, urllib, json, threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['fr']
		self.domains = ['torrent411.xyz']
		self.base_link = 'http://torrent411.xyz'
		self.search_link = '/torrents/search/?q=%s&cat=56'

	def _link(self, url, index):
		try:
			html = BeautifulSoup(client.request(url))
			html = html.find_all('div', class_ = 'details')[0]
			links = html.find_all('a')
			for link in links:
				if link['href'].startswith('magnet:'):
					self.tLock.acquire()
					self.tLinks[index] = link['href']
					break
		except:
			tools.Logger.error()
		finally:
			try: self.tLock.release()
			except: pass

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			data = self._decode(url)

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if 'tvshowtitle' in data:
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
						query = title
					else:
						if pack: query = '%s saison %d' % (title, season)
						else: query = '%s S%02d E%02d' % (title, season, episode) # Add space between season and episode, otherwise does not find anything.
				else:
					query = title # Do not include year, otherwise there are few results.
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			if not self._query(query): return sources

			url = self.base_link + self.search_link % urllib.quote_plus(query)
			html = BeautifulSoup(client.request(url))

			htmlTable = html.find_all('table', class_ = 'results')[0]
			htmlTable = htmlTable.find_all('tbody', recursive = False)[0]
			htmlRows = htmlTable.find_all('tr', recursive = False)

			self.tLock = threading.Lock()
			self.tLinks = [None] * len(htmlRows)
			threads = []
			for i in range(len(htmlRows)):
				urlTorrent = self.base_link + htmlRows[i].find_all('td', recursive = False)[1].find_all('a')[0]['href']
				threads.append(threading.Thread(target = self._link, args = (urlTorrent, i)))

			[thread.start() for thread in threads]
			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)
			while timer.elapsed() < timerEnd and any([thread.is_alive() for thread in threads]):
				tools.Time.sleep(0.5)

			self.tLock.acquire() # Just lock in case the threads are still running.
			for i in range(len(htmlRows)):
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				htmlRow = htmlRows[i]
				htmlColumns = htmlRow.find_all('td', recursive = False)

				# Name
				htmlName = htmlColumns[1].find_all('a')[0]['title']

				# Size
				htmlSize = htmlColumns[5].getText().strip().lower().replace('ko', 'kb').replace('mo', 'mb').replace('go', 'gb').replace('to', 'tb')

				# Link
				htmlLink = self.tLinks[i]

				# Seeds
				htmlSeeds = int(htmlColumns[7].getText().strip())

				# Metadata
				# Do not check/ignore, because this removes too many links. Titles also do not have the year on the website.
				meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

				# Add
				sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
			self.tLock.release()

			return sources
		except:
			return sources
