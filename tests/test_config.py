#!/usr/bin/env python

import os
import os.path
import stat
import ConfigParser

# Try out ConfigParser stuff

class ETClientAPIException(RuntimeError):
    pass
class ETClientAPIValueError(ETClientAPIException):
    pass
class ETClientAPINoDataException(ETClientAPIException):
    pass

def readOperator(cnfpath, db='Prod', readonly=True):
    section = "eT API reader"
    fieldname = "username"

    if not readonly:
        section = "eT API writer"
        fieldname = db + '_' + "writer"
        
    # Handle initial ~
    cnfExpanded = os.path.expanduser(cnfpath)
        
    # First check that file is sufficiently protected.  Only owner
    # should have access
    mode = os.stat(cnfExpanded).st_mode
    if (mode & (stat.S_IRWXG + stat.S_IRWXO)) != 0:
        raise ETClientAPIValueError, "Insufficiently protected config file"

    parser = ConfigParser.RawConfigParser()
    parser.read(cnfExpanded)
    username = parser.get(section, fieldname)
    return username

#  Main starts here

print "Try to open non-existent configuration file"
try:
    username = readOperator('nosuchfile.cnf')
    print "Got username ",username
except Exception,msg:
    print "failed with msg ",msg

print "/nTry to open unprotected file"
try:
    username = readOperator('/Users/jrb/.emacs')
    print "Got username ",username    
except Exception,msg:
    print "failed with msg ",msg

print "/nTry to get read-only username"
try:
    username = readOperator('~/.ssh/.etapi.cnf')
    print "Got username ",username    
except Exception,msg:
    print "failed with msg ",msg

print "/nTry to get write username for Raw"
try:
    username = readOperator('~/.ssh/.etapi.cnf', db='Raw', readonly=False)
    print "Got username ",username    
except Exception,msg:
    print "failed with msg ",msg
