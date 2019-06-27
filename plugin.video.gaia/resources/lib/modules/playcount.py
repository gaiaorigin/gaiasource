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


import json,sys,xbmc

from resources.lib.modules import control
from resources.lib.modules import trakt
from resources.lib.extensions import tools
from resources.lib.extensions import convert


def getMovieIndicators(refresh = False):
	try:
		if trakt.getTraktIndicatorsInfo() == True:
			return trakt.syncMoviesCache(cached = not refresh)
		else:
			from metahandler import metahandlers
			return metahandlers.MetaData(preparezip = False)
	except: pass


def getShowIndicators(refresh = False):
	try:
		if trakt.getTraktIndicatorsInfo() == True:
			return trakt.syncShowsCache(cached = not refresh)
		else:
			from metahandler import metahandlers
			return metahandlers.MetaData(preparezip = False)
	except: pass


def getSeasonIndicators(imdb, refresh = False):
	try:
		if trakt.getTraktIndicatorsInfo() == True:
			return trakt.syncSeasonsCache(imdb = imdb, cached = not refresh)
		else:
			from metahandler import metahandlers
			return metahandlers.MetaData(preparezip = False)
	except: pass


def getMovieOverlay(indicators, imdb):
	try:
		try:
			playcount = indicators._get_watched('movie', imdb, '', '')
			return str(playcount)
		except:
			playcount = [i for i in indicators if i == imdb]
			playcount = '7' if len(playcount) > 0 else 6
			return str(playcount)
	except:
		return '6'


def getMovieWatched(indicators, imdb):
	return int(getMovieOverlay(indicators, imdb)) == 7


def getShowOverlay(indicators, imdb, tvdb):
	try:
		try:
			playcount = indicators._get_watched('tvshow', imdb, '', '')
			return str(playcount)
		except:
			playcount = [i[0] for i in indicators if i[0] == tvdb and len(i[2]) >= int(i[1])]
			playcount = 7 if len(playcount) > 0 else 6
			return str(playcount)
	except:
		return '6'


def getShowWatched(indicators, imdb, tvdb):
	return int(getShowOverlay(indicators, imdb, tvdb)) == 7


def getSeasonOverlay(indicators, imdb, tvdb, season):
	try:
		try:
			playcount = indicators._get_watched('season', imdb, '', season)
			return str(playcount)
		except:
			playcount = [i for i in indicators if int(season) == int(i)]
			playcount = 7 if len(playcount) > 0 else 6
			return str(playcount)
	except:
		return '6'


def getSeasonWatched(imdb, tvdb, season, indicators = None):
	if indicators == None: indicators = getSeasonIndicators(imdb)
	return int(getSeasonOverlay(indicators, imdb, tvdb, season)) == 7


def getEpisodeOverlay(indicators, imdb, tvdb, season, episode):
	try:
		try:
			playcount = indicators._get_watched_episode({'imdb_id' : imdb, 'season' : season, 'episode': episode, 'premiered' : ''})
			return str(playcount)
		except:
			playcount = [i[2] for i in indicators if i[0] == tvdb]
			playcount = playcount[0] if len(playcount) > 0 else []
			playcount = [i for i in playcount if int(season) == int(i[0]) and int(episode) == int(i[1])]
			playcount = 7 if len(playcount) > 0 else 6
			return str(playcount)
	except:
		return '6'


def getEpisodeWatched(imdb, tvdb, season, episode, indicators = None):
	if indicators == None: indicators = getShowIndicators()
	return int(getEpisodeOverlay(indicators, imdb, tvdb, season, episode)) == 7


# Gaia
def getShowCount(indicators, imdb, tvdb, limit = False):
	try:
		if trakt.getTraktIndicatorsInfo() == False: raise Exception()
		result = trakt.showCount(imdb)
		if limit and result:
			result['unwatched'] = min(99, result['unwatched'])
		return result
	except:
		try:
			for indicator in indicators:
				if indicator[0] == tvdb:
					total = indicator[1]
					watched = len(indicator[2])
					unwatched = total - watched
					if limit: unwatched = min(99, unwatched)
					return {'total' : total, 'watched' : watched, 'unwatched' : unwatched}
		except: pass
		return None


# Gaia
def getSeasonCount(imdb, season = None, limit = False):
	try:
		if trakt.getTraktIndicatorsInfo() == False: raise Exception()
		result = trakt.seasonCount(imdb = imdb)
		if season == None:
			if limit and result:
				for i in range(len(result)):
					result[i]['unwatched'] = min(99, result[i]['unwatched'])
			return result
		else:
			result = result[int(season)]
			if limit: result['unwatched'] = min(99, result['unwatched'])
			return result
	except: pass
	return None


def markMovieDuringPlayback(imdb, tmdb, watched):
	try:
		if trakt.getTraktIndicatorsInfo() == False:
			raise Exception()

		setting = None

		watched = int(watched)
		watchedIs = watched == 7
		if watchedIs:
			# Only mark as watched if the previous watch is more than a week ago.
			# Trakt allows to mark an item with multiple watches, eg: watching a movie multiple times.
			# However, if the playback is stopped at almost the end of the stream and then finished a few days later, it will be marked watched multiple times.
			# Ignore these marks for items watched more than a week ago.

			allow = True
			setting = tools.Settings.getInteger('accounts.informants.trakt.watched')

			if setting == 0:
				try:
					watchedTime = trakt.watchedMoviesTime(imdb)
					watchedTime = convert.ConverterTime(value = watchedTime, format = convert.ConverterTime.FormatDateTimeJson).timestamp()
					currentTime = tools.Time.timestamp()
					differenceTime = currentTime - watchedTime
					allow = differenceTime > 604800
				except:
					pass
			elif setting == 1:
				trakt.markMovieAsNotWatched(imdb = imdb, tmdb = tmdb)

			if allow: trakt.markMovieAsWatched(imdb = imdb, tmdb = tmdb)
		else:
			trakt.markMovieAsNotWatched(imdb = imdb, tmdb = tmdb)

		trakt.syncMoviesCache()

		if (setting == None or setting == 1) and trakt.getTraktAddonMovieInfo() == True:
			trakt.markMovieAsNotWatched(imdb)
	except:
		pass

	try:
		from metahandler import metahandlers
		metaget = metahandlers.MetaData(preparezip = False)
		metaget.get_meta('movie', name = '', imdb_id = imdb)
		metaget.change_watched('movie', name = '', imdb_id = imdb, watched = watched)
	except:
		pass

	try:
		from resources.lib.extensions import trailer
		if watchedIs: trailer.Trailer().watch(imdb = imdb)
		else: trailer.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()


def markEpisodeDuringPlayback(imdb, tvdb, season, episode, watched):
	try:
		if trakt.getTraktIndicatorsInfo() == False:
			raise Exception()

		setting = None

		watched = int(watched)
		watchedIs = watched == 7
		if watchedIs:
			# Only mark as watched if the previous watch is more than a week ago.
			# Trakt allows to mark an item with multiple watches, eg: watching a movie multiple times.
			# However, if the playback is stopped at almost the end of the stream and then finished a few days later, it will be marked watched multiple times.
			# Ignore these marks for items watched more than a week ago.

			allow = True
			setting = tools.Settings.getInteger('accounts.informants.trakt.watched')

			if setting == 0:
				try:
					watchedTime = trakt.watchedShowsTime(tvdb, season, episode)
					watchedTime = convert.ConverterTime(value = watchedTime, format = convert.ConverterTime.FormatDateTimeJson).timestamp()
					currentTime = tools.Time.timestamp()
					differenceTime = currentTime - watchedTime
					allow = differenceTime > 604800
				except:
					pass
			elif setting == 1:
				trakt.markEpisodeAsNotWatched(imdb, tvdb, season, episode)

			if allow: trakt.markEpisodeAsWatched(imdb, tvdb, season, episode)
		else:
			trakt.markEpisodeAsNotWatched(imdb, tvdb, season, episode)

		trakt.syncShowsCache()

		if (setting == None or setting == 1) and trakt.getTraktAddonEpisodeInfo() == True:
			trakt.markEpisodeAsNotWatched(imdb, tvdb, season, episode)
	except:
		pass

	try:
		from metahandler import metahandlers
		metaget = metahandlers.MetaData(preparezip=False)
		metaget.get_meta('tvshow', name='', imdb_id=imdb)
		metaget.get_episode_meta('', imdb_id=imdb, season=season, episode=episode)
		metaget.change_watched('episode', '', imdb_id=imdb, season=season, episode=episode, watched=watched)
	except:
		pass

	try:
		from resources.lib.extensions import trailer
		if watchedIs: trailer.Trailer().watch(imdb = imdb)
		else: trailer.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()


def movies(imdb, tmdb, watched):
	watched = int(watched)
	watchedIs = watched == 7

	try:
		if trakt.getTraktIndicatorsInfo() == False: raise Exception()
		if watchedIs: trakt.watch(type = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, refresh = True, notification = False)
		else: trakt.unwatch(type = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, refresh = True, notification = False)
	except:
		pass

	try:
		from metahandler import metahandlers
		metaget = metahandlers.MetaData(preparezip = False)
		metaget.get_meta('movie', name = '', imdb_id = imdb)
		metaget.change_watched('movie', name = '', imdb_id = imdb, watched = watched)
		if trakt.getTraktIndicatorsInfo() == False: interface.Directory.refresh(position = True)
	except:
		pass

	try:
		from resources.lib.extensions import trailer
		if watchedIs: trailer.Trailer().watch(imdb = imdb)
		else: trailer.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()


def episodes(imdb, tvdb, season, episode, watched):
	watched = int(watched)
	watchedIs = watched == 7

	try:
		if trakt.getTraktIndicatorsInfo() == False: raise Exception()
		if watchedIs: trakt.watch(type = tools.Media.TypeEpisode, imdb = imdb, tvdb = tvdb, season = season, episode = episode, refresh = True, notification = False)
		else: trakt.unwatch(type = tools.Media.TypeEpisode, imdb = imdb, tvdb = tvdb, season = season, episode = episode, refresh = True, notification = False)
	except:
		pass

	try:
		from metahandler import metahandlers
		metaget = metahandlers.MetaData(preparezip = False)
		metaget.get_meta('tvshow', name = '', imdb_id = imdb)
		metaget.get_episode_meta('', imdb_id = imdb, season = season, episode = episode)
		metaget.change_watched('episode', '', imdb_id = imdb, season = season, episode = episode, watched = watched)
		if trakt.getTraktIndicatorsInfo() == False: tvshowsUpdate(imdb = imdb, tvdb = tvdb)
	except:
		pass

	try:
		from resources.lib.extensions import trailer
		if watchedIs: trailer.Trailer().watch(imdb = imdb)
		else: trailer.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()


def seasons(tvshowtitle, imdb, tvdb, season, watched):
	tvshows(tvshowtitle = tvshowtitle, imdb = imdb, tvdb = tvdb, season = season, watched = watched)


def tvshows(tvshowtitle, imdb, tvdb, season, watched):
	watched = int(watched)
	watchedIs = watched == 7

	try:
		from metahandler import metahandlers
		from resources.lib.indexers import episodes

		if not trakt.getTraktIndicatorsInfo() == False: raise Exception()

		name = control.addonInfo('name')

		dialog = control.progressDialogBG()
		dialog.create(str(name), str(tvshowtitle))
		dialog.update(0, str(name), str(tvshowtitle))

		metaget = metahandlers.MetaData(preparezip = False)
		metaget.get_meta('tvshow', name = '', imdb_id = imdb)

		items = episodes.episodes().get(tvshowtitle, '0', imdb, tvdb, idx = False)
		for i in range(len(items)):
			items[i]['season'] = int(items[i]['season'])
			items[i]['episode'] = int(items[i]['episode'])
		try: items = [i for i in items if int('%01d' % int(season)) == int('%01d' % i['season'])]
		except: pass
		items = [{'label': '%s S%02dE%02d' % (tvshowtitle, i['season'], i['episode']), 'season': int('%01d' % i['season']), 'episode': int('%01d' % i['episode'])} for i in items]

		count = len(items)
		for i in range(count):
			if xbmc.abortRequested == True: return sys.exit()
			dialog.update(int(100.0 / count * i), str(name), str(items[i]['label']))
			season, episode = items[i]['season'], items[i]['episode']
			metaget.get_episode_meta('', imdb_id = imdb, season = season, episode = episode)
			metaget.change_watched('episode', '', imdb_id = imdb, season = season, episode = episode, watched = watched)

		tvshowsUpdate(imdb = imdb, tvdb = tvdb)
		try: dialog.close()
		except: pass
	except:
		try: dialog.close()
		except: pass

	try:
		if trakt.getTraktIndicatorsInfo() == False: raise Exception()
		if watched == 7: trakt.watch(type = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, season = season, refresh = True, notification = False)
		else: trakt.unwatch(type = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, season = season, refresh = True, notification = False)
	except:
		tools.Logger.error()
		pass

	try:
		from resources.lib.extensions import trailer
		if watchedIs: trailer.Trailer().watch(imdb = imdb)
		else: trailer.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()


def tvshowsUpdate(imdb, tvdb):
	try:
		from metahandler import metahandlers
		from resources.lib.indexers import episodes

		if not trakt.getTraktIndicatorsInfo() == False: raise Exception()

		name = control.addonInfo('name')
		metaget = metahandlers.MetaData(preparezip = False)
		metaget.get_meta('tvshow', name = '', imdb_id = imdb)

		items = episodes.episodes().get('', '0', imdb, tvdb, idx = False)
		for i in range(len(items)):
			items[i]['season'] = int(items[i]['season'])
			items[i]['episode'] = int(items[i]['episode'])

		seasons = {}
		for i in items:
			if not i['season'] in seasons: seasons[i['season']] = []
			seasons[i['season']].append(i)

		countSeason = 0
		metaget.get_seasons('', imdb, seasons.keys()) # Must be called to initialize the database.
		for key, value in seasons.iteritems():
			countEpisode = 0
			for i in value: countEpisode += int(metaget._get_watched_episode({'imdb_id' : i['imdb'], 'season' : i['season'], 'episode': i['episode'], 'premiered' : ''}) == 7)
			countSeason += int(countEpisode == len(value))
			metaget.change_watched('season', '', imdb_id = imdb, season = key, watched = 7 if countEpisode == len(value) else 6)
		metaget.change_watched('tvshow', '', imdb_id = imdb, watched = 7 if countSeason == len(seasons.keys()) else 6)
	except:
		tools.Logger.error()
	interface.Directory.refresh(position = True)
