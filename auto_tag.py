import discogs_client
import collections
import fleep
import os
import eyed3
import mutagen
import requests
import time
from fuzzywuzzy import fuzz 
from fuzzywuzzy import process 
from mutagen.easyid3 import EasyID3
from difflib import SequenceMatcher
import pickle

d = discogs_client.Client('ExampleApplication/0.1', user_token="ppepOgrQAbykUIqSVvhkfVJacmtEBoKKrUzJogub")

class utils:


	@staticmethod
	def formattedArtists(release,trackObj):
		if (len(trackObj.artists) == 0 ):
			artistList = list(map( (lambda x: x.name), release.artists))
		else:
			artistList = list(map( (lambda x: x["name"]), trackObj.data["artists"]))
		return artistList

	
	
	#give file path to music file and return cleaned version
	@staticmethod
	def cleanFileName(filePath):
		fileName = os.path.splitext(os.path.basename(filePath))[0]
		#repalce these chars by whitespace
		badChars = ['-','_']
		cleanName = ""
		for char in fileName:
			if char in badChars:
				cleanName = cleanName + " "
			else:
				cleanName = cleanName + char
		#remove any words in filename without letters
		seperated = cleanName.split()
		cleanName = ""
		for word in seperated:
			if (any(c.isalpha() for c in word)):
				cleanName = cleanName + " " + word
		return cleanName

	#returns string of artist and title of song from its tags
	@staticmethod
	def tagsToString(filePath):
		audiofile = eyed3.load(filePath)
		return audiofile.tag.artist + " " + audiofile.tag.title
	
	@staticmethod	
	def tracksInFolder(folderPath):
		folderFiles = os.listdir(folderPath)
		trackPaths = []
		for folderFile in folderFiles:
			#path to current track
			trackPath = folderPath+"/"+folderFile
			#check if curr file is audio file
			audiofile = mutagen.File(trackPath)
			if not (audiofile == None):
				trackPaths.append(trackPath)
		return trackPaths

	@staticmethod	
	def folderToStrings(folderPath):
		fileFolderString = ""
		tagFolderString = ""
		trackPaths = utils.tracksInFolder(folderPath)
		for trackPath in trackPaths:
			fileFolderString = fileFolderString + ' ' + utils.cleanFileName(trackPath)
			tagFolderString = tagFolderString + " " + utils.tagsToString(trackPath)
		return tagFolderString, fileFolderString
	
	@staticmethod
	def filterNumTracks(releaseFolder, releaseObjDict):
		filteredReleaseObjDict = collections.OrderedDict()
		maxTracks = len(releaseFolder.tracks) + 1
		for releaseObj in releaseObjDict.items():
			if (len(releaseObj[1].tracklist) <= maxTracks):
				filteredReleaseObjDict[releaseObj[0]] = releaseObj[1]
		return filteredReleaseObjDict


	def mostHaveRelease(self, releases):
		if len(releases) > 0: 
			releases.sort(key=self.getHaves, reverse = True)
		return releases[0] 

	@staticmethod
	def subReleaseStringDict(filteredReleaseObjDict, allReleaseStringDict):
		filteredReleaseStringDict = collections.OrderedDict()
		for releaseObj in filteredReleaseObjDict.items():
			filteredReleaseStringDict[releaseObj[0]] = allReleaseStringDict[releaseObj[0]]
		return filteredReleaseStringDict	
	
	@staticmethod
	def getHaves(pReleaseID):
		release = (d.release(pReleaseID))
		time.sleep(0.1)
		haves = release.data['community']["have"]
		return haves

	@staticmethod
	#give release or track object and return string of all artists
	def artistsToString(track):
		toString = ""
		for artist in track.artists:
			toString = toString + artist.name + " "
			#toString.replace()
		return toString

class tagger:

	def __init__(self, lDir, labelID):
		self.lDir = lDir
		#self.releasesPaths = list(map( (lambda x : self.lDir + "/" + x), os.listdir(self.lDir)))
		self.releaseFolders = self.getReleaseFolders(self.lDir)
		self.labelID = labelID
		self.label = d.label(self.labelID)
		self.releaseObjDict = self.getLabelReleases()
		"""
		self.releases = self.getLabelReleases()
		with open('releases.pickle', 'wb') as f:
			pickle.dump(self.releases, f)
		
        with open("releases.pickle", 'rb') as f:
        	self.releases = pickle.load(f)
		"""

	#takes releaase object and makes string containing
	#a all artists from each track and the name of each track

	def getReleaseFolders(self, labelPath):
		releaseFolderPaths = list(map( (lambda x : labelPath + "/" + x), os.listdir(labelPath)))
		releaseFolder = []
		for releaseFolderPath in releaseFolderPaths:
			releaseFolder.append(release(releaseFolderPath))
		return releaseFolder

	def releaseToString(self, release):
		releaseString = ""
		numtracks = len(release.tracklist)
		for i in range (0, numtracks, 1):
			#time.sleep(.1)
			trackObj = release.tracklist[i]
			#get all artists from this track
			artist = ""
			if not (len(trackObj.artists) == 0):
				artist = tagger.artistsToString(trackObj)
			else:
				artist = tagger.artistsToString(release)
			releaseString = releaseString + " "  + artist + " " + trackObj.title
		#return string of all artists + all track names
		return releaseString

	@staticmethod
	#give release or track object and return string of all artists
	def artistsToString(track):
		toString = ""
		for artist in track.artists:
			toString = toString + artist.name + " "
		return toString
	
	#make String from a release's track
	def releaseTrackString(self, trackObj):
			artist = utils.artistsToString(trackObj)
			track = trackObj.title
			return artist + " " + track

	def getLabelReleases(self):
		releasesObj = self.label.releases
		numPages = releasesObj.pages
		releases = collections.OrderedDict()
		for i in range(0, numPages, 1):
			releasesPage = releasesObj.page(i)
			for release in releasesPage:
				time.sleep(0.100)
				releases[release.id] = release
		return releases

	"""get release with most Haves from list of release IDs"""
	def mostHaveRelease(self, releases):
		if len(releases) > 1: 
			releases.sort(key=self.getHaves, reverse = True)
		return self.releaseObjDict[releases[0]]
	
	"""
	def getHaves(pReleaseID):
		release = (d.release(pReleaseID))
		time.sleep(0.1)
		haves = release.data['community']["have"]
		return haves
	"""

	#get ordered dict of k=relId, v=releaseToString
	def allReleaseStringDict(self):
		releaseStringDict = collections.OrderedDict()
		for release in self.releaseObjDict.items():
			releaseStringDict[release[0]] = self.releaseToString(release[1])
			time.sleep(1)
		return releaseStringDict

	#return releaseIDs of closest matching releases 
	def findReleases(self, releaseFolder, releaseStringDict):
		highestScore = 0
		releaseIDs = []
		for release in releaseStringDict.items():
			score = fuzz.token_sort_ratio(releaseFolder.tagFolderString, release[1]) + fuzz.ratio(releaseFolder.fileFolderString,release[1])
			if score > highestScore:
				highestScore = score
				releaseIDs = [release[0]]
			elif (score == highestScore):
				releaseIDs.append(release[0])
		return releaseIDs

	""" args: release ID - int ; return: haves - int
		desc: Obtain number of people owning release from releaseID"""
	def getHaves(self, releaseID):
		return self.releaseObjDict[releaseID].data["community"]["have"]

	#build dict of key=folderpath value=folderString
	def allFoldersToStringDict(self):
		folderPathDict = collections.OrderedDict()
		for folder in self.releaseFolders:
			folderString = utils.folderToStrings(folder.path)
			folderPathDict[folder.path] = folderString
		return folderPathDict

	#find right track obj for tagging the track file
	def findTrack(self, trackPath, release):
		fileNameString = utils.cleanFileName(trackPath)
		tagString = utils.tagsToString(trackPath)
		score = 0
		trackObj = None
		for track in release.tracklist:
			trackScore = fuzz.token_set_ratio(self.releaseTrackString(track),fileNameString) + fuzz.token_set_ratio(self.releaseTrackString(track),tagString)
			if (trackScore > score):
				trackObj = track
				score = trackScore
		return trackObj
	
	
	def setAlbumArt(self, trackPath, release):
		if (len(release.data["images"]) == 0):
			return
		url = release.data["images"][0]["resource_url"]
		artPath = os.path.dirname(trackPath) + "/" + url.split('/')[-1]
		r = requests.get(url, allow_redirects=True)
		open(artPath, 'wb').write(r.content)
		audio = mutagen.id3.ID3(trackPath)
		with open(artPath, 'rb') as albumart:
			audio['APIC'] = mutagen.id3.APIC( encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=albumart.read() )
		audio.save()

	#tag track given its path, trackObject and the releaseObject
	def tagTrack(self, trackPath, trackObj, release):
		audiofile = mutagen.easyid3.EasyID3(trackPath)
		audiofile['album'] = (release.data["labels"][0]['catno'] + " - " + release.data["title"])
		audiofile['albumartist'] = release.data["artists_sort"]
		audiofile['artist'] = utils.formattedArtists(release,trackObj)
		audiofile['date'] = (release.data["released_formatted"])
		audiofile['genre'] = (release.data["styles"])
		audiofile['title'] = trackObj.title
		audiofile['tracknumber'] = trackObj.position
		audiofile.save()
		self.setAlbumArt(trackPath,release)

	#tag all tracks in a folder
	def tagFolder(self, folderPath, release):
		tracks = utils.tracksInFolder(folderPath)
		for trackPath in tracks:
			trackObj = self.findTrack(trackPath, release)
			self.tagTrack(trackPath, trackObj, release)
	
	#tag the whole label folder
	def tag(self):
		
		allReleaseStringDict = self.allReleaseStringDict()
		

		with open('dwxString.pickle', 'wb') as f:
			pickle.dump(allReleaseStringDict, f)
		"""
		with open("releases.pickle", 'rb') as f:
			releaseStrings = pickle.load(f)
		"""

		for releaseFolder in self.releaseFolders:

            #get release Obj with similar #tracks
			filteredReleaseObjDict = utils.filterNumTracks(releaseFolder, self.releaseObjDict)
            #get releaseStringDict from releaseObjDict
			filteredReleaseStringDict = utils.subReleaseStringDict(filteredReleaseObjDict, allReleaseStringDict)
            #get release IDs matching folder best
			releaseIDs = self.findReleases(releaseFolder, filteredReleaseStringDict)
            #select release with most amount of Haves
			releaseObj = self.mostHaveRelease(releaseIDs)
			#releaseObj = self.releaseObjDict[releaseIDs[0]]
			releaseFolder.tag(releaseObj)

class release:
	def __init__(self, path):
		self.path = path
		self.tracks = self.getTracks(self.path)
		self.tagFolderString, self.fileFolderString = self.folderToString()

	def folderToString(self):
		fileFolderString = ""
		tagFolderString = ""
		for track in self.tracks:
			fileFolderString = fileFolderString + " " + track.cName
			tagFolderString = tagFolderString + " " + track.tName
		return tagFolderString, fileFolderString

	def setReleaseObj(self, releaseObj):
		self.releaseObj = releaseObj

	def getTracks(self, folderPath):
	    folderFiles = os.listdir(folderPath)
	    trackPaths = []
	    for folderFile in folderFiles:
            #path to current track
	        trackPath = folderPath+"/"+folderFile
            #check if curr file is audio file
	        audiofile = mutagen.File(trackPath)
	        if not (audiofile == None):
	        	trackPaths.append(track(trackPath))
	    return trackPaths
    
	def tag(self, releaseObj):
	    self.releaseObj = releaseObj
	    for track in self.tracks:
	        trackObj = track.findTrack(releaseObj)
	        track.tag(trackObj, releaseObj)


class track:
	def __init__(self, path):
	    self.path = path
	    self.dName = os.path.splitext(os.path.basename(self.path))[0]
	    self.cName = self.cleanFileName(self.dName)
	    self.tName = self.tagsToString(self.path)

	def findTrack(self, release):
		score = 0
		trackObj = None
		for track in release.tracklist:
			trackScore = fuzz.token_set_ratio(self.releaseTrackString(track),self.cName) + fuzz.token_set_ratio(self.releaseTrackString(track),self.tName)
			if (trackScore > score):
				trackObj = track
				score = trackScore
		return trackObj
    
	def tag(self, trackObj, releaseObj):
		audiofile = mutagen.easyid3.EasyID3(self.path)
		audiofile['album'] = (releaseObj.data["labels"][0]['catno'] + " - " + releaseObj.data["title"])
		audiofile['albumartist'] = releaseObj.data["artists_sort"]
		audiofile['artist'] = utils.formattedArtists(releaseObj,trackObj)
		audiofile['date'] = (releaseObj.data["released_formatted"])
		audiofile['genre'] = (releaseObj.data["styles"])
		audiofile['title'] = trackObj.title
		audiofile['tracknumber'] = trackObj.position
		audiofile.save()
		self.setAlbumArt(releaseObj)

	def setAlbumArt(self, releaseObj):
		if releaseObj.images == None:
		#if (len(releaseObj.data["images"]) == 0):
			return None
		url = releaseObj.data["images"][0]["resource_url"]
		artPath = os.path.dirname(self.path) + "/" + url.split('/')[-1]
		r = requests.get(url, allow_redirects=True)
		open(artPath, 'wb').write(r.content)
		audio = mutagen.id3.ID3(self.path)
		with open(artPath, 'rb') as albumart:
			audio['APIC'] = mutagen.id3.APIC( encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=albumart.read() )
		audio.save()

	def tagsToString(self, filePath):
		audiofile = eyed3.load(filePath)
		return audiofile.tag.artist + " " + audiofile.tag.title

	#make String from a release's track
	def releaseTrackString(self, trackObj):
			artist = self.artistsToString(trackObj)
			track = trackObj.title
			return artist + " " + track

	"""
	Args:
	track - discogs track Obj | track to obtain artists from
	Returns:
	toString - String | all artists separated by " "
	Description:
	Returns string of all artists from discogs track obj
	"""
	def artistsToString(self, track):
		toString = ""
		for artist in track.artists:
			toString = toString + artist.name + " "
		return toString

	"""
	Args: 
	path - string | path of audio file to clean
	Returns:
	String | the cleaned file name (without extension)
	"""
	def cleanFileName(self, path):
		fileName = os.path.splitext(os.path.basename(path))[0]
		#replace these chars by whitespace
		badChars = ['-','_']
		cleanName = ""
		for char in fileName:
			if char in badChars:
				cleanName = cleanName + " "
			else:
				cleanName = cleanName + char
		#remove any words in filename without letters
		seperated = cleanName.split()
		cleanName = ""
		for word in seperated:
			if (any(c.isalpha() for c in word)):
				cleanName = cleanName + " " + word
		return cleanName


#dtp = tagger("./dtp", 9098)
#dtp.tag()

dwx = tagger("./dwx", 74109)
dwx.tag()