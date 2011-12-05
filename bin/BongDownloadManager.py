#!/usr/bin/env python
"""
Bong.tv Download Manager

Checks bong.tv online-VCR for recorded shows, moves video files and metadata 
to local storage and deletes recording from Bong Space after successful download
"""
import BongSingleton
import BongEnvironment
import BongDownload

def main():
    BongSingleton.terminateScriptIfAlreadyRunning()
    BongEnvironment.initializeEnvironment(__file__)
    
    BongEnvironment.LogScriptStart()
    
    BongDownload.work()
    
    BongEnvironment.LogScriptTermination()
    
if __name__ == "__main__":
    main()


