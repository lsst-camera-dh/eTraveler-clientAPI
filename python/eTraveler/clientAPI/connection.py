'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
import requests
from sys import stdout
#  Might want to specify path or a use a different name for commands module
#  to avoid possibility of getting the wrong one
import eTraveler.clientAPI.commands

class Connection:
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler/'
    devServerUrl='http://srs.slac.stanford.edu/eTraveler/'

    API = {
        'registerHardware' : ['htype', 'site', 'location', 'experimentSN', 
                              'manufacturerId', 'model', 'manufactureDate',
                              'manufacturer', 'operator', 'quantity'],
        'defineHardwareType' : ['name', 'description', 'sequenceWidth',
                                'isBatched'],
        'runHarnessed' : ['hardwareId', 'travelerName',
                         'travelerVersion', 'hardwareGroup', 'site',
                          'jhInstall', 'operator']
        }
    APIdefaults = { 
        'runHarnessed' : {'operator' : None, 'travelerVersion' : ''}, 
        'defineHardwareType' : {'sequenceWidth' : 4, 'isBatched' : 0},
        'registerHardware' : {'experimentSN' : '', 'manufacturerId' : '', 
                              'model' : '',
                              'manufactureDate' : '', 'manufacturer' : '',
                              'operator' : None, 'quantity' : 1} }
        
        
    def __init__(self, operator=None, db='Prod', prodServer=True, 
                 exp='LSST-CAMERA', debug=False):
        url = Connection.prodServerUrl
        if not prodServer: url = Connection.devServerUrl
        # For now can't talk to CDMS databases
        #url += ('/exp/' + exp + '/')
        url += db 
        url += '/Results/'
        self.baseurl = url
        #self.dsmode = 'dataSourceMode=' + db
        # if operator is None, prompt or use login?
        # do something for authorization
        self.operator = operator
        self.debug = debug
        if debug:
            print " baseurl is ", str(self.baseurl)
            print "Operator is ", str(self.operator)
        else:
            print "baseurl is ", str(self.baseurl)

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
        #if self.debug:
        print 'query before jsonification is ', str(query)

        jdata = json.dumps(query)
        print 'after jsonification: \n', str(jdata)
        if self.debug: return None

        posturl = self.baseurl + command
        print "about to post to ", posturl
        r = requests.post(posturl, data = jdata)
        # or could just do r = requests.post(self.baseurl, json=query)

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

        if type(rsp) is dict:
            if rsp['acknowledge'] == None:
                return rsp['hardwareId']
            else:
                print 'str rsp of acknowledge: '
                print  str(rsp['acknowledge'])
                raise Exception, rsp['acknowledge']
        else:
            print 'return value of unexpected type', type(rsp)
            print 'return value cast to string is: ', str(rsp)
            raise Exception, str(rsp)

    def runHarnessed(self, **kwds):
        '''
        Run specified traveler on specified component.
        Traveler must be automatable
        
        Return status
        '''

        rsp = self._make_query('runAutomatable', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None, 'command' : 'lcatr-harness with options'}

        if rsp['acknowledge'] == None:
            if self.debug:
                print 'Next we should execute the command string: '
                print rsp['command']
            else:
                clientAPI.commands.execute(rsp['command'], out = stdout.write)
            return
        else:
            raise Exception, rsp['acknowledge']
