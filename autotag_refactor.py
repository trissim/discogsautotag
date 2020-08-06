import discogs_api
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

d = discogs_api.Client('ExampleApplication/0.1', user_token="ppepOgrQAbykUIqSVvhkfVJacmtEBoKKrUzJogub")

class tostr:

        """
        args: 
        path - string | path of audio file to clean
        returns:
        string | the cleaned file name (without extension)
        """
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
        def folderToStringFileNames(trackPaths):
                fileFolderString = ""
                tagFolderString = ""
                for trackPath in trackPaths:
                        fileFolderString += ' ' + tostr.cleanFileName(trackPath)
                return fileFolderString

        @staticmethod
        def folderToStringTags(trackPaths):
                tagFolderString = ""
                for trackPath in trackPaths:
                        tagFolderString += " " + tostr.tagsToString(trackPath)
                return tagFolderString

        @staticmethod
        def folderToStrings(trackPaths):
            return folderToStringTags(trackPaths), folderToStringFileNames(trackPaths)

        """
        Args:
        track - discogs track Obj | track to obtain artists from
        Returns:
        toString - String | all artists separated by " "
        Description:
        Returns string of all artists from discogs track obj
        """
        @staticmethod
        def artistsString(track):
                toString = ""
                for artist in track.artists:
                        toString = toString + artist.name + " "
                        #toString.replace()
                return toString

        @staticmethod
        def releaseString(release):
                releaseString = ""
                numtracks = len(release.tracklist)
                for i in range (0, numtracks, 1):
                        #time.sleep(.1)
                        trackObj = release.tracklist[i]
                        #get all artists from this track
                        artist = ""
                        if not (len(trackObj.artists) == 0):
                                artist = tostr.artistsString(trackObj)
                        else:
                                artist = tostr.artistsString(release)
                        releaseString = releaseString + " "  + artist + " " + trackObj.title
                #return string of all artists + all track names
                return releaseString

        #make String from a release's track
        @staticmethod
        def releaseTrackString(trackObj):
                        artist = tostr.artistsString(trackObj)
                        track = trackObj.title
                        return artist + " " + track




class utils:

        @staticmethod
        def formattedArtists(release,trackObj):
                if (len(trackObj.artists) == 0 ):
                        artistList = list(map( (lambda x: x.name), release.artists))
                else:
                        artistList = list(map( (lambda x: x["name"]), trackObj.data["artists"]))
                return artistList

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
        def filterNumTracks(releaseFolder, releaseObjDict):
                filteredReleaseObjDict = collections.OrderedDict()
                maxTracks = len(releaseFolder.tracks) + 1
                for relid, releaseObj in releaseObjDict.items():
                        if (len(releaseObj.tracklist) <= maxTracks):
                                filteredReleaseObjDict[relid] = releaseObj
                return filteredReleaseObjDict


        @staticmethod
        def mostHaveRelease(releases):
                if len(releases) > 1:
                        releases.sort(key=utils.getHaves, reverse = True)
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

        #get ordered dict of k=relId, v=releaseToString
        @staticmethod
        def labelReleaseStringDict(releaseObjDict):
                releaseStringDict = collections.OrderedDict()
                for release in releaseObjDict.items():
                        releaseStringDict[release[0]] = tostr.releaseString(release[1])
                        time.sleep(1)
                return releaseStringDict

        @staticmethod
        def labelReleaseDict(label):
                releasesObj = label.releases
                numPages = releasesObj.pages
                releases = collections.OrderedDict()
                for i in range(0, numPages, 1):
                        releasesPage = releasesObj.page(i)
                        for release in releasesPage:
                                time.sleep(0.100)
                                releases[release.id] = release
                return releases


class tagger:

        def __init__(self, labelDir, labelID,load_pickle=None, save_pickle = False):
                self.labelDir = labelDir
                #self.releasesPaths = list(map( (lambda x : self.lDir + "/" + x), os.listdir(self.lDir)))
                self.releaseFolders = self.getReleaseFolders(self.labelDir)
                self.labelID = labelID
                self.label = d.label(self.labelID)
                if not load_pickle is None:
                    with open(load_pickle, 'rb') as f:
                        self.releaseObjDict = pickle.load(f)
                else:
                    self.releaseObjDict = utils.labelReleaseDict(self.label)

                if save_pickle:
                    with open('releases.pickle', 'wb') as f:
                        pickle.dump(self.releaseObjDict, f)


        #takes releaase object and makes string containing
        #a all artists from each track and the name of each track
        def getReleaseFolders(self, labelPath):
                releaseFolderPaths = list(map( (lambda x : labelPath + "/" + x), os.listdir(labelPath)))
                releaseFolders = []
                for releaseFolderPath in releaseFolderPaths:
                        releaseFolders.append(release(releaseFolderPath))
                return releaseFolders


        #return releaseIDs of closest matching releases 
        def findReleases(self, releaseFolder, releaseStringDict):
                releaseIDs = []
                highestScore = 0
                """
                invertedStringDict = {value: key for key, value in releaseStringDict.items()}
                releaseStrings = list(releaseStringDict.values())
                matches = process.extract("new york jets", choices, limit=2,scorer=fuzz.token_sort_ratio)
                for match in matches:
                    releaseIDs.append(invertedStringDict[match])
                return releaseIDs
                """
                for relid, release_str in releaseStringDict.items():
                        score = fuzz.token_sort_ratio(releaseFolder.tagFolderString, release_str) + fuzz.ratio(releaseFolder.fileFolderString, release_str)
                        if score > highestScore:
                                highestScore = score
                                releaseIDs = [relid]
                        elif (score == highestScore):
                                releaseIDs.append(relid)
                return releaseIDs

        #tag the whole label folder
        def tag(self):
                allReleaseStringDict = utils.labelReleaseStringDict()

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
                        releaseObj = utils.mostHaveRelease(releaseIDs)
                        #releaseObj = self.releaseObjDict[releaseIDs[0]]
                        releaseFolder.tag(releaseObj)

class release:
        def __init__(self, path):
                self.path = path
                self.tracks = utils.tracksInFolder(self.path)
                self.tagFolderString = tostr.folderToStringFileNames(self.tracks)
                self.fileFolderString = tostr.folderToStringTags(self.tracks)

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
            for track in self.tracks:
                trackObj = track.findTrack(releaseObj)
                track.tag(trackObj, releaseObj)


class track:
        def __init__(self, path):
            self.path = path
            self.dName = os.path.splitext(os.path.basename(self.path))[0]
            self.cName = tostr.cleanFileName(self.dName)
            self.tName = tostr.tagsToString(self.path)

        def findTrack(self, release):
                score = 0
                trackObj = None
                for track in release.tracklist:
                        trackScore = fuzz.token_set_ratio(tostr.releaseTrackString(track),self.cName) + fuzz.token_set_ratio(tostr.releaseTrackString(track),self.tName)
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
                if releaseObj.images is None:
                        return None
                url = releaseObj.data["images"][0]["resource_url"]
                artPath = os.path.dirname(self.path) + "/" + url.split('/')[-1]
                r = requests.get(url, allow_redirects=True)
                open(artPath, 'wb').write(r.content)
                audio = mutagen.id3.ID3(self.path)
                with open(artPath, 'rb') as albumart:
                        audio['APIC'] = mutagen.id3.APIC( encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=albumart.read() )
                audio.save()


#dtp = tagger("./dtp", 9098)
#dtp.tag()

dwx = tagger("./dwx", 74109)
dwx.tag()
