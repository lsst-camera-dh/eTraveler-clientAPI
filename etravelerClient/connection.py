'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
from urllib import urlencode
from urllib2 import urlopen

class Connection(Object):
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler/'
    devServerUrl='http://scalnx-v04.slac.stanford.edu:8180/eTraveler/'

    API = {
        'registerHardware' : ['operator', 'htype', 'site', 'location',
        'experimentSN', 'manufacturerId', 'model', 'manufactureDate'],
        'runAutomatable' : ['operator', 'hardwareId', 'travelerName',
                         'travelerVersion', 'hardwareGroup']
        }
    APIdefaults = { 'runAutomatable' : { }, 
        'registerHardware' : {'manufacturerId' : '', 'model' : '',
                              'manufactureDate' : '' }  }
        
        
    def __init__(self, operator=None, db='Prod', prodServer=True, 
                 exp='LSST-CAMERA'):
        url = prodServerUrl
        if not prodServer: url = devServerUrl
        # For now can't talk to CDMS databases
        #url += ('/exp/' + exp + '/')
        url += db 
        self.baseurl = url
        #self.dsmode = 'dataSourceMode=' + db
        # if operator is None, prompt
        # do something for authorization
        self.op = operator


####
    def make_params(self, command, **kwds):
        '''
        Take keyword arguments and return dictionary suitable for use
        with command or raise ValueError.
        '''
        cfg = dict(kwds)
        want = set(API[command])
        missing = want.difference(cfg)
        missingCopy = set(missing)
        for f in missing:
            if f in set(APIdefaults[command]) :
                cfg.uptdate(f=APIdefaults[command][f])
                missing.remove(f)
        if missingCopy:
            msg = 'Not given enough info to statisfy eTraveler API for %s: missing: %s' % (command, str(sorted(missingCopy)))
            log.error(msg)
            raise ValueError, msg
        query = {k:cfg[k] for k in want}
        return query

    def make_query(self, command, **kwds):
        '''
        Make a query string for the given command and with the given
        keywords or raise ValueError.
        '''
        query = self.make_params(command,**kwds)

        jdata = json.dumps(query)
        qdata = urlencode({'jsonObject':jdata})
        log.debug('Query eTraveler "%s" with json="%s", query="%s"' % (command, jdata, qdata))

        #url = self.lims_url + command
        url = self.baseurl
        
        fp = urlopen(url, data=qdata)
        page = fp.read()
        try:
            jres = json.loads(page)
        except ValueError, msg:
            msg = 'Failed to load return page with qdata="%s" url="%s" got: "%s" (JSON error: %s)' %\
                (qdata, url, page, msg)
            print msg
            log.error(msg)
            raise
        return jres
        
    def registerHardware(self, **kwds):
        '''
          Register a new hardware component; return its id
        '''
        jres = self.make_query('registerHardware', kwds)
        
        # extract the returned id from jres
        return hid

    def runTraveler(self, **kwds):
        '''
        Run specified traveler on specified component.
        Traveler must be automatable
        Return status
        '''
        jres = self.make_query('runTraveler', kwds)
        
        # extract the returned status from jres
        return status

        
