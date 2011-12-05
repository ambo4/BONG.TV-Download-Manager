"""
BongDownload


"""
import sys
import sqlite3
import time
import os
import os.path
import BongEnvironment
import BongAPI
import BongLibrary
from urlgrabber.grabber import URLGrabber, URLGrabError


def downloadFile(url, filename, subdir):
    BongEnvironment.logger.info("starting download of {!s} to {!s}/{!s}".format(url, subdir, filename))
    maxBytesPerSecond=0        #  2**19   ==> 0.5 MByte/s 
                               #  0       ==> not restricted
    grabber = URLGrabber( progress_obj=None
                        , throttle=maxBytesPerSecond        
                        , reget='simple'
                        , retry=5
                        , retrycodes=[-1,4,5,6,7,12,14]
                        , timeout=30
                        , user_agent='bong download manager/1.0'
                        )
    
    statinfo = os.stat(BongEnvironment.settings['recdir'])
    
    targetdir = os.path.join(BongEnvironment.settings['recdir'], subdir)
    if not os.path.isdir(targetdir):
        os.mkdir(targetdir)
        if os.name == 'posix':
            os.chmod(targetdir, 0777)
            os.chown(targetdir, statinfo.st_uid, statinfo.st_gid)

    targetfile = os.path.join(targetdir, filename)
    
    t1 = time.time()
    try:
        local_filename = grabber.urlgrab(url, targetfile)
    except URLGrabError, e:
        BongEnvironment.logger.warning('exception {!s} trying to download {!s} to {!s}'.format(e, url, targetfile))
        return False
    t2 = time.time()

    if local_filename != targetfile:
        BongEnvironment.logger.warning("local_filename {!r} <> targetfile {!r}".format(local_filename, targetfile))
        return False
        
    if not os.path.isfile(targetfile):
        BongEnvironment.logger.warning("file {!r} not found".format(targetfile))
        return False
    else:
        if os.name == 'posix':
            os.chmod(targetfile, 0666)
            os.chown(targetfile, statinfo.st_uid, statinfo.st_gid)
    
    sz = os.path.getsize(local_filename)
    
    BongEnvironment.logger.info("Download completed. Speed = {!s} byte/second, File size = {!s} bytes, Duration = {!s} seconds".format(float(sz)/float(t2-t1), sz, t2-t1))

    return True


def work():
    
    bong = BongAPI.BongApi()
    
    if bong.checkCredentials():
        
        # prevIDs hold the list recording ids previously processed
        # newIDs holds the list of recording ids to be processed
        # if we get the same list of ids as before, we are risking an endless while loop
        prevIDs = bong.getSetOfIds()
        
        while bong.refreshDatabase():
            newIDs = bong.getSetOfIds()
            if newIDs != prevIDs:
                prevIDs = newIDs.copy()
                
                for id, kv in bong.recordings.items(): 
                    subdir = "bong{0:06d}".format(kv['db_id'])
                    if kv['downloadHQ']:
                        if downloadFile(kv['downloadHQ'], BongLibrary.renameResource(kv['downloadHQ'], 'video_hq'), subdir):
                            if kv['image'] and kv['image_name']:
                                downloadFile(kv['image'], BongLibrary.renameResource(kv['image'], 'image'), subdir)
                            bong.registerDownload(id)
                            bong.deleteRecording(id)
            else:
                BongEnvironment.logger.warning("Breaking out of an infinite loop trying to process the same recordings repeatedly")
                break
    else:
        BongEnvironment.logger.warning("Username and password not valid")    


