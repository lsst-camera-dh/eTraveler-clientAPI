'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
import requests
import sys
import os
import string
#  Might want to specify path or a use a different name for commands module
#  to avoid possibility of getting the wrong one
import eTraveler.clientAPI.commands

def to_terminal(out):
    print out

class Connection:
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler/'
    devServerUrl='http://srs.slac.stanford.edu/eTraveler/'

    API = {
        'registerHardware' : ['htype', 'site', 'location', 'experimentSN', 
                              'manufacturerId', 'model', 'manufactureDate',
                              'manufacturer', 'operator', 'quantity'],
        'defineHardwareType' : ['name', 'description', 'subsystem',
                                'sequenceWidth', 'batchedFlag', 'operator'],
        'runHarnessedById' : ['hardwareId', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator'],
        'runHarnessed'     : ['experimentSN', 'htype', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator'],
        'defineRelationshipType' : ['name', 'description', 'hardwareTypeName',
                                    'minorTypeName', 'numItems', 'slotNames',
                                    'operator'],
        'defineRelationshipTypeById' : ['name', 'description', 'hardwareTypeId',
                                        'minorTypeId', 'numItems', 'slotNames',
                                        'operator'],
        'validateYaml' : ['contents', 'validateOnly', 'operator'],
        'uploadYaml' : ['contents', 'reason', 'responsible',
                        'validateOnly', 'operator'],
        'setHardwareStatus' : ['experimentSN', 'htype','attributeName','reason',
                               'adding', 'activityId', 'operator'],
        'adjustHardwareLabel' : ['experimentSN','htype', 'attributeName',
                                 'adding', 'reason', 'activityId', 'operator'],
        }
    APIdefaults = { 
        'runHarnessedById' : {'operator' : None, 'travelerVersion' : ''}, 
        'runHarnessed' : {'operator' : None, 'travelerVersion' : ''}, 
        'defineHardwareType' : {'sequenceWidth' : 4, 'batchedFlag' : 0,
                                'subsystem' : 'Default', 'operator' : None},
        'registerHardware' : {'experimentSN' : '', 'manufacturerId' : '', 
                              'model' : '',
                              'manufactureDate' : '', 'manufacturer' : '',
                              'operator' : None, 'quantity' : 1},
        'defineRelationshipType' : {'operator' : None, 'numItems' : 1,
                                    'description' : None},
        'defineRelationshipTypeById' : {'operator' : None, 'numItems' : 1,
                                        'description' : None},
        'validateYaml' : {'operator' : None, 'validateOnly' : 'true'},
        'uploadYaml' : {'operator' : None, 'validateOnly' : 'false'},
        'setHardwareStatus' : {'operator' : None, 'reason' : 'Set via API',
                               'adding' : 'NA', 'activityId' : None},
        'adjustHardwareLabel' : {'operator' : None, 'adding' : 'true',
                                 'reason' : 'Adjusted via API',
                                 'activityId' : None},
        }
        
        
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

    def __make_params(self, func, **kwds):
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
            msg = 'Not given enough info to satisfy eTraveler API for %s: missing: %s' % (func, str(sorted(missingCopy)))
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

    def __make_query(self, command, func, **kwds):
        '''
        Make a query string for the given command and with the given
        keywords or raise ValueError.

        Arugments
        command - the command sent to eTraveler front-end. Required
        func - user function calling us. Determines what is in kwds
        kwds - parameters for command going to eTraveler
        '''
        # make a dict of parameters
        query = self.__make_params(func, **kwds)
        jdata = json.dumps(query)

        posturl = self.baseurl + command

        if self.debug:
            if 'slotNames' in kwds:
                print 'Value of slotNames: '
                print kwds['slotNames']
            print "json string: "
            print str(jdata)
            if command == 'defineRelationshipType':
                print 'Original query string: '
                print str(query)
                #print 'In debug mode go no further for now'
                #return
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
            print "Content type: ", r.headers['content-type']
            print "Text: ", r.text
            print "this is type of what I got: ", type(r)
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
        rsp = self.__make_query('registerHardware', 'registerHardware',
                                **kwds)

        return self._decodeResponse('registerHardware', rsp)

    def defineHardwareType(self, **kwds):
        '''
        Define a new hardware type.  Keyword arguments are
            name   - required.  Name of new type.  May not have 
                embedded blanks or certain other special characters
            description - optional but strongly recommended!
            subsystem - short name for subsystem 
            sequenceWidth - # of digits in auto-generated serial numbers
                defaults to 4.  Value of 0 means "don't auto-generate"
            subsystem - defaults to 'Default'
            batchedFlag - defaults to 0  (false)

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
        rsp = self.__make_query('defineHardwareType', 'defineHardwareType',
                                **kwds)

        return self._decodeResponse('defineHardwareType', rsp)
        
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
        rsp = self.__make_query('runAutomatable', 'runHarnessedById', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None, 'command' : 'lcatr-harness with options'}
        harnessedCommand = self._decodeResponse('runAutomatable', rsp)
        if self.debug:
            print 'Next we should execute the command string: '
            print harnessedCommand

        eTraveler.clientAPI.commands.execute(harnessedCommand, 
                                             env = self.env,
                                             out = to_terminal)

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

        rsp = self.__make_query('runAutomatable', 'runHarnessed', **kwds)
        if self.debug:
            rsp = {'acknowledge' : None, 'command' : 'lcatr-harness with options'}

        harnessedCommand = self._decodeResponse('runAutomatable', rsp)
        if self.debug:
            print 'Next we should execute the command string: '
            print harnessedCommand

        eTraveler.clientAPI.commands.execute(harnessedCommand, 
                                             env = self.env,
                                             out = to_terminal)

    def defineRelationshipType(self, **kwds):
        '''
        Create new relationship type, specifying hardware types by name.
        Arguments:
            name - name of new type. Required
            description - optional but strongly recommended
            hardwareTypeName - name of "major" type
            minorTypeName - name of subsidiary type
            numItems - defaults to 1
            slotNames - single string or list of strings
        Returns:
            If successful, new id
        '''
        revisedKwds = self.__check_slotnames(**kwds)
        rsp = self.__make_query('defineRelationshipType', 
                                'defineRelationshipType',
                                **revisedKwds)
        return self._decodeResponse('defineReleationshipType', rsp)

    def defineRelationshipTypeById(self, **kwds):
        '''
        Create new relationship type, specifying hardware types by id.
        Arguments:
            name - name of new type. Required
            description - optional but strongly recommended
            hardwareTypeId - id of "major" type
            minorTypeId - id of subsidiary type
            numItems - defaults to 1
            slotNames - single string or list of strings
        '''
        revisedKwds = self.__check_slotnames(**kwds)
        rsp = self.__make_query('defineRelationshipType', 
                                'defineRelationshipTypeById',
                                **revisedKwds)
        return self._decodeResponse('defineRelationshipType', rsp)

    def validateYaml(self, **kwds):
        '''
        Check that supplied traveler definition follows YAML syntax,
        uses only allowed keywords, and is compatible with database
        specified in connection (insofar as that can be confirmed without
        actual ingest).
        Keyword Arguments:
            filepath - file containing YAML
                   OR
            contents - YAML to be ingested as a string
        Return: String 'Success' if operation succeeded, else error msg
        '''
        k = dict(kwds)
        rqst = dict({})
        cmd = 'uploadYaml'
        rqst = self._reviseContents(k)
        #print rqst['contents']
        rsp = self.__make_query(cmd, 'validateYaml', **rqst)
        return self._decodeResponse(cmd, rsp)

    def uploadYaml(self, **kwds):
        '''
        Validates as above, then ingests traveler into db associated 
        with connection.

        Keyword Arguments:
            filepath - file containing YAML
                   OR
            content - YAML to be ingested as a string
            responsible - responsible person for this traveler. Defaults
                          to operator
            reason - non-empty string describing purpose of traveler 
                     and/or reason for new version
                    
        Return: String 'Success' if operation succeeded, else error msg
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'uploadYaml'
        rqst  = self._reviseContents(k)
        if 'responsible' in k: rqst['responsible'] = k['responsible']
        else: rqst['responsible'] = self.operator
        if 'reason' in k: rqst['reason'] = k['reason']
        rsp = self.__make_query(cmd, 'uploadYaml', **rqst)
        return self._decodeResponse(cmd, rsp)
    
    def __check_slotnames(self, **kwds):
        '''
        Looks for properly formatted and consistent values for 
        numItems and slotNames.  In case there are multiple
        slotNames, reformat as single string.
        Return new argument dict
        '''
        k = dict(kwds)
        num = 1
        if 'numItems' in k:
            num = int(k['numItems'])
        if 'slotNames' not in k:
            raise ValueError, 'Missing slotName argument'

        slist = k['slotNames']

        if isinstance(slist, str): slist = [slist]

        if not isinstance(slist, list):
            raise ValueError, 'Improper slotName list'
        for e in slist: 
            if not isinstance(e, str):
                raise ValueError, 'Slot names must be strings'
            if ',' in e:
                raise ValueError, 'Slot names may not contain commas'

        if (len(slist) != 1) and (len(slist) != num):
            raise ValueError, 'Wrong number of slotnames'

        kwds['slotNames'] = string.join(slist, ',')
        return kwds

    def _reviseContents(self, k):
        if 'contents' in k:
            return k
        elif 'filepath' in k:
            cnt = ''
            fp = k.pop('filepath')
            with open(fp) as f:
                for line in f:
                    cnt += line
                k['contents'] = cnt
        else:
            raise ValueError, 'No input yaml. Use contents or filepath keyword'
        return k
            
    def _decodeResponse(self, command, rsp):
        '''
        Common error handling for response to query. If good response,
        differentiate by command issued
        '''
        if type(rsp) is dict:
            if rsp['acknowledge'] == None:
                if (command == 'runAutomatable'): return rsp['command']
                elif (command == 'uploadYaml'): return 'Success'
                else: return rsp['id']
            else:
                #print 'str rsp of acknowledge: '
                #print  str(rsp['acknowledge'])
                raise Exception, rsp['acknowledge']
        else:
            print 'return value of unexpected type', type(rsp)
            print 'return value cast to string is: ', str(rsp)
            raise Exception, str(rsp)
