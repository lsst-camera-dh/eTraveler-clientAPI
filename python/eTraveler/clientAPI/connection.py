'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
import requests
import sys
import os
#  Might want to specify path or a use a different name for commands module
#  to avoid possibility of getting the wrong one
import eTraveler.clientAPI.commands

def to_terminal(out):
    print out

class Connection:
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler/'
    devServerUrl='http://srs.slac.stanford.edu/eTraveler/'
    #devServerUrl='http://scalnx-v04.slac.stanford.edu:8180/eTraveler/'

    API = {
        'registerHardware' : ['htype', 'site', 'location', 'experimentSN', 
                              'manufacturerId', 'model', 'manufactureDate',
                              'manufacturer', 'operator', 'quantity'],
        'defineHardwareType' : ['name', 'description', 'sequenceWidth',
                                'batchedFlag', 'operator'],
        'runHarnessedById' : ['hardwareId', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator'],
        'runHarnessed'     : ['experimentSN', 'htype', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator'],

        }
    APIdefaults = { 
        'runHarnessedById' : {'operator' : None, 'travelerVersion' : ''}, 
        'runHarnessed' : {'operator' : None, 'travelerVersion' : ''}, 
        'defineHardwareType' : {'sequenceWidth' : 4, 'batchedFlag' : 0,
                                'operator' : None},
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
        # if operator is None, prompt or use login?
        # do something for authorization
        self.operator = operator
        self.debug = debug
        self.env = dict(os.environ)
        if debug:
            print " baseurl is ", str(self.baseurl)
            print "Operator is ", str(self.operator)

    def _make_params(self, func, **kwds):
        '''
        Take keyword arguments and return dictionary suitable for use
        with func or raise ValueError.
        '''
        if func not in Connection.API:
            raise KeyError, 'eTraveler API does not support function %s' % str(func)
        cfg = dict(kwds)
        if not 'operator' in cfg:
            cfg['operator'] = None
        want = set(Connection.API[func])
        missing = want.difference(cfg)
        missingCopy = set(missing)
        for f in missing:
            if f in set(Connection.APIdefaults[func]) :
                cfg.update(f=Connection.APIdefaults[func][f])
                missingCopy.remove(f)
        if missingCopy:
            msg = 'Not given enough info to statisfy eTraveler API for %s: missing: %s' % (func, str(sorted(missingCopy)))
            #log.error(msg)
            raise ValueError, msg
        if cfg['operator'] == None:
            if self.operator == None:
                raise ValueError, 'Missing parameter: must specify operator'
            cfg['operator'] = self.operator

        for k in want:
            if k not in cfg:
                cfg[k] = Connection.APIdefaults[func][k]
        query = {k:cfg[k] for k in want}
        return query

    def _make_query(self, command, func, **kwds):
        '''
        Make a query string for the given command and with the given
        keywords or raise ValueError.

        Arugments
        command - the command sent to eTraveler front-end. Required
        func - user function calling us. Determines what is in kwds
        kwds - parameters for command going to eTraveler
        '''
        # make a dict of parameters
        query = self._make_params(func, **kwds)
        jdata = json.dumps(query)

        posturl = self.baseurl + command

        if self.debug:
            print "json string: "
            print str(jdata)
            print "about to post to ", posturl

        try:
            r = requests.post(posturl, data = {"jsonObject" : jdata})
        except requests.HTTPError, msg:
            print "HTTPError: ", str(msg)
            sys.exit()
        except requests.RequestException, msg:
            print "Some other exception: ", str(msg)
            sys.exit()

        if self.debug:
            print 'No exceptions! '
            print "Status code: ", r.status_code
            print "Content type: ", r.headers['content-type']
            print "Text: ", r.text
            print "this is type of what I got: ", type(r)

        try:
            rsp = r.json()
            return rsp
        except ValueError, msg:
            # for now just reraise
            print "Unable to decode json"
            print "Original: ", str(r)
            raise ValueError, msg

        
    def registerHardware(self, **kwds):
        '''
          Register a new hardware component; return its id
          Keyword arguments are
          htype  - new type name; required
          site   - site where registered component is; required
          location - location at site where registered component is; required
          experimentSN - serial number for new component.  Required if
                    serial numbers are not auto-generated; ignored if they are
          quantity - defaults to 1.  Ignored for non-batch types
          Remaining keyword arguments are optional and default to empty string
           manufacturerId, model, manufactureDate, manufacturer
        '''
        rsp = self._make_query('registerHardware', 'registerHardware',
                               **kwds)
        
        if type(rsp) is dict:
            if rsp['acknowledge'] == None:
                return rsp['id']
            else:
                print 'str rsp of acknowledge: '
                print  str(rsp['acknowledge'])
                raise Exception, rsp['acknowledge']
        else:
            print 'return value of unexpected type', type(rsp)
            print 'return value cast to string is: ', str(rsp)
            raise Exception, str(rsp)

    def defineHardwareType(self, **kwds):
        '''
        Define a new hardware type.  Keyword arguments are
            name   - required.  Name of new type.  May not have 
                embedded blanks or certain other special characters
            description - optional but strongly recommended!
            sequenceWidth - # of digits in auto-generated serial numbers
                defaults to 4.  Value of 0 means "don't auto-generate"
            isBatched - defaults to False

        Returns:
            id of new hardware type if successful, else raises exception
        '''
        k = dict(kwds)
        if 'name' not in k:
            raise ValueError, 'missing name parameter'

        # validate input
        badchars = ' $()/\\&<?'
        nm = k['name']
        for c in badchars:
            if c in nm:
                if c == ' ':
                    raise ValueError, 'No blanks allowed in hardware type name'
                else:
                    raise ValueError, 'name contains disallowed character %s' %c
        rsp = self._make_query('defineHardwareType', 'defineHardwareType',
                               **kwds)

        if type(rsp) is dict:
            if rsp['acknowledge'] == None:
                return rsp['id']
            else:
                print 'str rsp of acknowledge: '
                print  str(rsp['acknowledge'])
                raise Exception, rsp['acknowledge']
        else:
            print 'return value of unexpected type', type(rsp)
            print 'return value cast to string is: ', str(rsp)
            raise Exception, str(rsp)
        
    def runHarnessedById(self, **kwds):
        '''
        Run specified traveler on specified component.
        Traveler must be automatable
        Arguments: 
            hardwareId  - returned from call to registerHardware. Required
            travelerName - required
            travelerVersion - defaults to most recent active version
            hardwareGroup - required
            site         - Site of job harness installation. Required
            jhInstall    - Name of job harness installation. Required
        Return status
        '''

        rsp = self._make_query('runAutomatable', 'runHarnessedById', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None, 'command' : 'lcatr-harness with options'}

        if rsp['acknowledge'] == None:
            if self.debug:
                print 'Next we should execute the command string: '
                print rsp['command']

            eTraveler.clientAPI.commands.execute(rsp['command'], 
                                                 env = self.env,
                                                 out = to_terminal)
            return
        else:
            raise Exception, rsp['acknowledge']


    def runHarnessed(self, **kwds):
        '''
        Run specified traveler on specified component.
        Traveler must be automatable
        Arguments: 
            experimentSN  - Experiment serial number. Required
            hardwareType  - Required
            travelerName - Required
            travelerVersion - defaults to most recent active version
            hardwareGroup - required
            site         - Site of job harness installation. Required
            jhInstall    - Name of job harness installation. Required
        Return status
        '''

        rsp = self._make_query('runAutomatable', 'runHarnessed', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None, 'command' : 'lcatr-harness with options'}

        if rsp['acknowledge'] == None:
            if self.debug:
                print 'Next we should execute the command string: '
                print rsp['command']

            eTraveler.clientAPI.commands.execute(rsp['command'], 
                                                 env = self.env,
                                                 out = to_terminal)
            return
        else:
            raise Exception, rsp['acknowledge']
