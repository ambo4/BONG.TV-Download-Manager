"""
Functions to prevent concurrent execution of the Bong Download Manager

If more than one instance of the Bong Download Manager are executed at the 
same time, they might get in the way of each other. To ensure that there
is only one instance running, these functions try to acquire exclusive
access to an operating system resource for the duration of the process.
A second instance fails to get hold of the same resource and terminates.

Ensuring exclusive execution is the first action in the main script
"""
import sys
import socket

def terminateIfTcpIpPortInUse(port=40738):
    """
    Use a listening TCP/IP socket to ensure exclusive execution of the current script
    
    The operating system allows only one process to listen on a port. Therefore
    we try to use a predefined port. If we succeed, no other instance of this
    script is running. Otherwise False is returned to terminate script execution.
    
    We are listening only on the loopback interface 127.0.0.1 so that the open
    port is not exposed on the network. The port number may be altered to a 
    value in the range 1025..65536. Check against IANA assigned port numbers 
    to avoid conflicts with known server ports. 
    """
    retval = False
    try:
        # make the socket variable global so it never goes out of 
        # scope until the end of the process. At the end of the
        # process the socket is closed during garbage collection 
        global lockingSocket
        lockingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lockingSocket.bind(('127.0.0.1', port))
        lockingSocket.listen(1)
        retval = True
    except socket.error:
        print "Another instance of this script is already active (TCP/IP port {!s} is in use).".format(port)
    except:
        print "Oops, something went wrong while binding and listening on TCP/IP port {!s}".format(port)
        for msg in sys.exc_info():
            print msg
    return retval

def terminateScriptIfAlreadyRunning():
    if not terminateIfTcpIpPortInUse():
        print "Terminating script execution"
        sys.exit(1)

