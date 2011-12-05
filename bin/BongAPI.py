import os
import os.path
import sys
import sqlite3
import time
import codecs
import urllib
import urllib2
import logging
import xml.etree.cElementTree as ET
import BongEnvironment
from BongLibrary import unicode_string, bongDateTimeToSqlite, bongTimeToSqlite, unescape

class BongApi:
    """description of class"""

    def _et_node_text(self, etnode, etpath, default=''):
        """
        element tree helper function to select a sub-element of the 
        given node and return the text of the selected element
        """
        node = etnode.find(etpath)
        if node is None:
            return default
        else:
            return unescape(node.text)


    def __init__(self):
        self.recordings = {}
        self.username = BongEnvironment.settings['bong_username']
        self.password = BongEnvironment.settings['bong_password']
        self.server = BongEnvironment.settings['bong_server']
        self.reccat = ( "id"
                      , "title"
                      , "subtitle"
                      , "description"
                      , "channel"
                      , "genre"
                      , "start"
                      , "duration"
                      , "image_name"
                      , "image"
                      , "series_season"
                      , "series_number"
                      , "series_count"
                      , "downloadHQ")
        self.cacheLifeSpan = 30 

    def getSetOfIds(self):
        return set(self.recordings.keys())
        
    
    def dumpRecordings(self, bong_id=""):
        if not self.recordings:
            return False
        
        allattr = set()
        for id, kv in self.recordings.items():
            allattr.union(set(kv.keys()))
        reqattr = set(self.reccat)
        addattr = allattr - reqattr
        
        orderedkeys = list(self.reccat)
        if addattr:
            addattr = list(addattr)
            addattr.sort()
            BongEnvironment.logger.info(u"the list of recordings contains additional attributes: {!s}".format(addattr))
            orderedkeys.extend(addattr)

        if bong_id != "" and bong_id in self.recordings.keys():
            selected = {bong_id: self.recordings[bong_id]}
        else:
            selected = self.recordings.copy()     
        
        BongEnvironment.logger.info(u"-"*60)
        
        for id, kv in selected.items():
            BongEnvironment.logger.info(u"values for recording {!s}".format(id))
            for k in orderedkeys:
                if k in kv.keys():
                    BongEnvironment.logger.info(u"{} = {!r}".format(k, kv[k]))
            BongEnvironment.logger.info(u"-"*60)

    
    def useCachedResponse(self, cachefile):
        lifespan = BongEnvironment.settings['cacheLifeSpan']
        if 0 < lifespan:
            fn = BongEnvironment.settings[cachefile]
            if os.path.isfile(fn):
                if (time.time() - os.path.getmtime(fn)) < lifespan:
                    return True
        return False
    
    def getCachedResponse(self, cachefile):
        fn = BongEnvironment.settings[cachefile]
        with codecs.open(fn, "r", "utf-8") as f:
            return f.read() 
        
    def cacheResponse(self, cachefile, xmldata):
        fn = BongEnvironment.settings[cachefile]
        with codecs.open(fn,'w','utf-8') as f:
            f.write(xmldata)
    
    def killCachedResponse(self, cachefile):
        fn = BongEnvironment.settings[cachefile]
        if os.path.isfile(fn):
            os.remove(fn)
        
    def getRecordings(self):
    
        self.recordings.clear()
        
        if self.useCachedResponse('getRecordingsCache'):
            xmldata = self.getCachedResponse('getRecordingsCache')
            BongEnvironment.logger.info(u"using cached response for getRecordings()")
            #BongEnvironment.logger.info(unicode_string(xmldata))
            tree = ET.fromstring(xmldata)
        else:
            url = "http://{server}/api/recordings.xml?{credentials}".format( server = self.server
                                                                           , credentials = urllib.urlencode({ 'username' : self.username
                                                                                                            , 'password' : self.password }))
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            if response.code != 200:
                BongEnvironment.logger.warning(url)
                BongEnvironment.logger.warning("request failed ({code!s} {message!s})".format( code = response.code
                                                                                  , message = response.msg ))
                return False

            BongEnvironment.logger.info("{req} -> ({code!s} {message!s})".format( req = url
                                                                     , code = response.code
                                                                     , message = response.msg ))
            xmldata = response.read()
            BongEnvironment.logger.info(unicode_string(xmldata))
        
            tree = ET.fromstring(xmldata)

            if self._et_node_text(tree, "status", "false") != 'true':
                BongEnvironment.logger.warning("response contains errors.")
                return False
            else:
                self.cacheResponse('getRecordingsCache', xmldata)

        # find all recording elements with an id sub-element
        for rec in tree.findall("recording/[id]"):
            id = self._et_node_text(rec, "id")
            if 0 < len(id):
                recitems = {}
                self.recordings[id] = recitems
                for item in rec:
                    if item.tag != u"files":
                        recitems[item.tag] = unescape(item.text)
                for media in rec.findall("files/file"):
                    if self._et_node_text(media, "type") == 'download':
                        if self._et_node_text(media, "quality") == 'HQ':
                            recitems["downloadHQ"] = self._et_node_text(media, "url")
                        elif self._et_node_text(media, "quality") == 'NQ':
                            recitems["downloadNQ"] = self._et_node_text(media, "url")
                for name in self.reccat:
                    if not name in recitems:
                        BongEnvironment.logger.warning("missing element {} in recording {}".format(name, id))
                        return False
        return True

    def checkCredentials(self):

        if self.useCachedResponse('checkCredentialsCache'):
            xmldata = self.getCachedResponse('checkCredentialsCache')
            BongEnvironment.logger.info(u"using cached response for checkCredentials")
            #BongEnvironment.logger.info(unicode_string(xmldata))
            tree = ET.fromstring(xmldata)
        else:
            url = "http://{server}/api/users.xml?{credentials}".format( server = self.server
                                                                      , credentials = urllib.urlencode({ 'username' : self.username
                                                                                                       , 'password' : self.password }))
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            if response.code != 200:
                BongEnvironment.logger.warning(url)
                BongEnvironment.logger.warning("request failed ({code!s} {message!s})".format( code = response.code
                                                                                  , message = response.msg ))
                return False

            BongEnvironment.logger.info("{req} -> ({code!s} {message!s})".format( req = url
                                                                     , code = response.code
                                                                     , message = response.msg ))
            xmldata = response.read()
            BongEnvironment.logger.info(unicode_string(xmldata))
            tree = ET.fromstring(xmldata)

            if self._et_node_text(tree, "status", "false") != 'true':
                BongEnvironment.logger.warning("response contains errors.")
                return False
            else:
                self.cacheResponse('checkCredentialsCache', xmldata)

        return True ;


    def deleteRecording(self, recordingID):
        url = "http://{server}/api/recordings/{id}/delete.xml?{credentials}".format( server = self.server
                                                                                   , id = recordingID
                                                                                   , credentials = urllib.urlencode({ 'username' : self.username
                                                                                                                    , 'password' : self.password }))
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        self.killCachedResponse('getRecordingsCache')

        if response.code != 200:
            BongEnvironment.logger.warning(url)
            BongEnvironment.logger.warning("request failed ({code!s} {message!s})".format( code = response.code
                                                                              , message = response.msg ))
            return False

        BongEnvironment.logger.info("{req} -> ({code!s} {message!s})".format( req = url
                                                                 , code = response.code
                                                                 , message = response.msg ))
        xmldata = response.read()
        BongEnvironment.logger.info(unicode_string(xmldata))
        tree = ET.fromstring(xmldata)

        if self._et_node_text(tree, "status", "false") != 'true':
            BongEnvironment.logger.warning("response contains errors.")
            return False

        return True ;


    def registerDownload(self, bong_id):
        con = sqlite3.connect(BongEnvironment.settings['dbfile'])
        BongEnvironment.logger.info("opening database to mark recording {!s} as downloaded".format(bong_id))
        con.execute("update recording set download_state = 0 where bong_id = :bong_id", {"bong_id": bong_id})
        con.commit()
        con.close()     
    
    
    def refreshDatabase(self):
        fieldnames = ( "bong_id"
                     , "title"
                     , "subtitle"
                     , "description"
                     , "genre"
                     , "channel"
                     , "start"
                     , "duration"
                     , "series_season"
                     , "series_number"
                     , "series_count"
                     , "image_name"
                     , "image"
                     , "downloadHQ"
                     , "downloadNQ"
                     ) 
        sql = """
              INSERT 
              INTO    recording 
                     ( is_downloadable
                     , download_state
                     , bong_id
                     , title
                     , subtitle
                     , description
                     , genre
                     , channel
                     , start
                     , duration
                     , series_season
                     , series_number
                     , series_count
                     , image_name
                     , image
                     , downloadHQ
                     , downloadNQ
                     ) 
              VALUES ( 'Y'
                     , 1
                     ,:bong_id
                     ,:title
                     ,:subtitle
                     ,:description
                     ,:genre
                     ,:channel
                     ,:start
                     ,:duration
                     ,:series_season
                     ,:series_number
                     ,:series_count
                     ,:image_name
                     ,:image
                     ,:downloadHQ
                     ,:downloadNQ
                     )
                 """

        con = sqlite3.connect(BongEnvironment.settings['dbfile'])
        BongEnvironment.logger.info("opening database to update available recordings")

        con.execute("update recording set is_downloadable = 'N'")
        con.commit()

        self.getRecordings()

        for id, kv in self.recordings.items():

            self.dumpRecordings(id)    

            w = {}
            for fn in fieldnames:
                if kv.has_key(fn):
                    if fn == 'start':
                        # start = '23-11-2011 20:15'
                        #     --> '2011-11-23 20:15:00'
                        w['start'] = bongDateTimeToSqlite(kv['start'])
                        if w['start'] is None:
                            BongEnvironment.logger.warning("start timestamp missing or malformed: {!s}".format(kv['start']))
                    elif fn == 'duration':
                        # duration = '1:50'
                        #       --> '01:50:00'
                        w['duration'] = bongTimeToSqlite(kv['duration'])
                        if w['duration'] is None:
                            BongEnvironment.logger.warning("duration missing or malformed: {!s}".format(kv['duration']))
                    else:
                        w[fn] = kv[fn]
                else:
                    if fn == 'bong_id':
                        w['bong_id'] = kv['id']
                    else:
                        w[fn] = None

            cur = con.cursor()
            cur.execute("select id, download_state from recording where bong_id = :bong_id", {"bong_id": id})
            rec = cur.fetchone() 
            cur.close()
            
            if rec: 
                kv['db_id'] = rec[0]
                if 0 == rec[1]:
                    BongEnvironment.logger.info(u"recording with bong_id {!s} has already been downloaded".format(id))
                    del self.recordings[id]
                else:
                    BongEnvironment.logger.info(u"existing record for bong_id {!s} found".format(id))
                    con.execute("update recording set is_downloadable = 'Y' where bong_id = :bong_id", {"bong_id": id})
                    con.commit()
            else:
                cur = con.cursor()
                try:
                    cur.execute(sql, w)
                    kv['db_id'] = cur.lastrowid
                    con.commit()
                    BongEnvironment.logger.info(u"new record for bong_id {!s} inserted".format(id))
                except:
                    BongEnvironment.logger.info(u"insert with bong_id {!s} failed:".format(id))
                    for x in sys.exc_info():
                        BongEnvironment.logger.info(x)
                cur.close()

        con.close()     
        
        return (0 < len(self.recordings))