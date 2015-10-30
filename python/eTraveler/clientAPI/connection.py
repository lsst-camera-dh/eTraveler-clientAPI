'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
import requests

class Connection:
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler/'
    devServerUrl='http://scalnx-v04.slac.stanford.edu:8180/eTraveler/'

    API = {
        'registerHardware' : ['htype', 'site', 'location', 'experimentSN', 
                              'manufacturerId', 'model', 'manufactureDate',
                              'operator'],
        'runAutomatable' : ['hardwareId', 'travelerName',
                         'travelerVersion', 'hardwareGroup', 'operator']
        }
    APIdefaults = { 'runAutomatable' : {'operator' : None }, 
        'registerHardware' : {'manufacturerId' : '', 'model' : '',
                              'manufactureDate' : '', 'operator' : None }  }
        
        
    def __init__(self, operator=None, db='Prod', prodServer=True, 
                 exp='LSST-CAMERA', debug=False):
        url = Connection.prodServerUrl
        if not prodServer: url = Connection.devServerUrl
        # For now can't talk to CDMS databases
        #url += ('/exp/' + exp + '/')
        url += db 
        self.baseurl = url
        #self.dsmode = 'dataSourceMode=' + db
        # if operator is None, prompt
        # do something for authorization
        self.operator = operator
        self.debug = debug
        if debug:
            print "Destination url is ", str(self.baseurl)
            print "Operator is ", str(self.operator)


####
    def _make_params(self, command, **kwds):
        '''
        Take keyword arguments and return dictionary suitable for use
        with command or raise ValueError.
        '''
        if command not in Connection.API:
            raise KeyError, "eTraveler API does not support command " + str(command);
        cfg = dict(kwds)
        if not 'operator' in cfg:
            cfg['operator'] = None
        want = set(Connection.API[command])
        missing = want.difference(cfg)
        missingCopy = set(missing)
        for f in missing:
            if f in set(Connection.APIdefaults[command]) :
                cfg.update(f=Connection.APIdefaults[command][f])
                missingCopy.remove(f)
        if missingCopy:
            msg = 'Not given enough info to statisfy eTraveler API for %s: missing: %s' % (command, str(sorted(missingCopy)))
            #log.error(msg)
            raise ValueError, msg
        if cfg['operator'] == None:
            if self.operator == None:
                raise ValueError, 'Missing parameter: must specify operator'
            cfg['operator'] = self.operator

        for k in want:
            if k not in cfg:
                cfg[k] = Connection.APIdefaults[command][k]
        query = {k:cfg[k] for k in want}
        return query

    def _make_query(self, command, **kwds):
        '''
        Make a query string for the given command and with the given
        keywords or raise ValueError.
        '''
        query = self._make_params(command,**kwds)
        if self.debug:
            print 'query before jsonification is ', str(query)

        jdata = json.dumps(query)
        if self.debug: return None

        r = requests.post(url, data=jdata)
        # or could just do r = requests.post(url, json=query)

        # Now to look at the response:
        try:
            rsp = r.json
            return rsp
        except ValueError, msg:
            # for now just reraise
            print "Unable to decode json"
            raise ValueError, msg

        
    def registerHardware(self, **kwds):
        '''
          Register a new hardware component; return its id
        '''
        rsp = self._make_query('registerHardware', **kwds)
        
        if self.debug:
            rsp = {'hardwareId': 17, 'acknowledge' : None}

        if rsp['acknowledge'] == None:
            return rsp['hardwareId']
        else:
            raise Exception, rsp['acknowledge']

    def runTraveler(self, **kwds):
        '''
        Run specified traveler on specified component.
        Traveler must be automatable
        Return status
        '''
        rsp = self._make_query('runAutomatable', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None}

        if rsp['acknowledge'] == None:
            return
        else:
            raise Exception, rsp['acknowledge']

        
