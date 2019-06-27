# GAIA

import sys
import xbmc
import xbmcvfs

try: action = sys.argv[1]
except: action = 'load'

pathFrom = 'special://skin/shortcuts/'
pathTo = 'special://userdata/addon_data/script.skinshortcuts/'
extensionOld = '.gaia.old'
extensionNew = '.gaia.new'

dirs, files = xbmcvfs.listdir(pathFrom)

if action == 'load':
	
	for file in files:
		try:
			fileTo = pathTo + file
			fileGaiaOld = fileTo + extensionOld
			fileGaiaNew = fileTo + extensionNew
			
			if xbmcvfs.exists(fileTo):
				xbmcvfs.copy(fileTo, fileGaiaOld)
				xbmcvfs.delete(fileTo)
			
			'''if xbmcvfs.exists(fileGaiaNew):
				xbmcvfs.copy(fileGaiaNew, fileTo)
			else:
				fileFrom = pathFrom + file
				xbmcvfs.copy(fileFrom, fileTo)'''
			
			fileFrom = pathFrom + file
			xbmcvfs.copy(fileFrom, fileTo)
		except:
			pass

elif action == 'unload':
	
	for file in files:
		try:
			if not file.endswith(extensionOld) and not file.endswith(extensionNew):
				fileTo = pathTo + file
				fileGaiaOld = fileTo + extensionOld
				fileGaiaNew = fileTo + extensionNew
				
				if xbmcvfs.exists(fileGaiaNew):
					xbmcvfs.delete(fileGaiaNew)
					
				xbmcvfs.copy(fileTo, fileGaiaNew)
				
				if xbmcvfs.exists(fileGaiaOld):
					xbmcvfs.delete(fileTo)
					xbmcvfs.copy(fileGaiaOld, fileTo)
					xbmcvfs.delete(fileGaiaOld)
		except:
			pass