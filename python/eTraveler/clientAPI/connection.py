'''
Class for storing connection/configuration information
and handling communication at bottom layer
'''
import time
import json
import requests
import sys
import os
import os.path
import stat
import string
import datetime

# Note: need to change to configparser for python3
import ConfigParser

from dateutil.parser import parse as parsetime

#  Might want to specify path or a use a different name for commands module
#  to avoid possibility of getting the wrong one
import eTraveler.clientAPI.commands

def to_terminal(out):
    print outd

class ETClientAPIException(RuntimeError):
    pass
class ETClientAPIValueError(ETClientAPIException):
    pass
class ETClientAPINoDataException(ETClientAPIException):
    pass

class Connection:
    prodServerUrl='http://lsst-camera.slac.stanford.edu/eTraveler'
    devServerUrl='http://lsst-camera-dev.slac.stanford.edu/eTraveler'
    localServerUrl='http://localhost:8084/eTraveler'

    
    API = {
        'registerHardware' : ['htype', 'site', 'location', 'experimentSN', 
                              'manufacturerId', 'model', 'manufactureDate',
                              'manufacturer', 'operator', 'quantity',
                              'remarks','cnfPath'],
        'defineHardwareType' : ['name', 'description', 'subsystem',
                                'sequenceWidth', 'batchedFlag', 'operator',
                                'cnfPath'],
        'runHarnessedById' : ['hardwareId', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator', 'cnfPath'],
        'runHarnessed'     : ['experimentSN', 'htype', 'travelerName',
                              'travelerVersion', 'hardwareGroup', 'site',
                              'jhInstall', 'operator', 'cnfPath'],
        'defineRelationshipType' : ['name', 'description', 'hardwareTypeName',
                                    'minorTypeName', 'numItems', 'slotNames',
                                    'operator', 'cnfPath'],
        'defineRelationshipTypeById' : ['name', 'description', 'hardwareTypeId',
                                        'minorTypeId', 'numItems', 'slotNames',
                                        'operator', 'cnfPath'],
        'validateYaml' : ['contents', 'validateOnly', 'operator'],
        'uploadYaml' : ['contents', 'reason', 'responsible',
                        'validateOnly', 'operator', 'cnfPath'],
        'setHardwareStatus' : ['experimentSN', 'hardwareTypeName',
                               'hardwareStatusName','reason',
                               'adding', 'activityId', 'operator','cnfPath'],
        'modifyHardwareLabel' : ['experimentSN', 'hardwareTypeName',
                                 'labelName', 'labelGroupName', 'reason',
                                 'adding', 'activityId', 'operator', 'cnfPath'],
        'adjustHardwareLabel' : ['experimentSN','hardwareTypeName',
                                 'hardwareStatusName', 'cnfPath',
                                 'adding', 'reason', 'activityId', 'operator'],
        'setHardwareLocation' : ['experimentSN', 'hardwareTypeName',
                                 'locationName', 'siteName', 'reason',
                                 'activityId', 'operator', 'cnfPath'],
        'getHardwareHierarchy' : ['experimentSN', 'hardwareTypeName',
                                  'noBatched', 'timestamp', 'operator'],
        'getContainingHardware' : ['experimentSN', 'hardwareTypeName',
                                   'timestamp', 'operator'],
        'getRunInfo' : ['activityId', 'operator'],
        'getManufacturerId' : ['experimentSN', 'hardwareTypeName',
                               'operator'],
        'setManufacturerId' : ['experimentSN', 'hardwareTypeName',
                               'manufacturerId', 'reason', 'operator'],
        'getRunResults' : ['function', 'run', 'stepName', 'schemaName',
                           'filterKey', 'filterValue', 'operator'],
        'getRunFilepaths' : ['function', 'run', 'stepName', 'operator'],
        'getResultsJH'  : ['function', 'travelerName', 'hardwareType',
                           'stepName', 'schemaName', 'model', 'experimentSN',
                           'filterKey', 'filterValue', 'hardwareLabels',
                           'operator'],
        'getFilepathsJH'  : ['function', 'travelerName', 'hardwareType',
                             'stepName', 'model', 'experimentSN',
                             'hardwareLabels', 'operator'],
        'getManualRunResults' : ['function', 'run', 'stepName', 'operator'],
        'getManualRunFilepaths' : ['function', 'run','stepName', 'operator'], 
        'getManualRunSignatures' : ['function', 'run','stepName',
                                    'activityStatus', 'operator'], 
        'getManualResultsStep' : ['function', 'travelerName', 'hardwareType',
                                  'stepName', 'model', 'experimentSN',
                                  'hardwareLabels', 'operator'],
        'getManualFilepathsStep' : ['function', 'travelerName', 'hardwareType',
                                    'stepName', 'model', 'experimentSN',
                                    'hardwareLabels', 'operator'],
        'getManualSignaturesStep' : ['function', 'travelerName', 'hardwareType',
                                     'stepName', 'model', 'experimentSN',
                                     'hardwareLabels', 'activityStatus',
                                     'operator'],
        'getActivity'     : ['function', 'activityId', 'operator'],
        'getRunActivities' : ['function', 'run', 'operator'],
        'getRunSummary' : ['function', 'run', 'operator'],
        'getComponentRuns' : ['function', 'hardwareType', 'experimentSN',
                              'operator', 'travelerName'],
        'getHardwareInstances' : ['function', 'hardwareType',
                                  'experimentSN', 'model', 'hardwareLabels',
                                  'operator'],
        }
    APIdefaults = { 
        'runHarnessedById' : {'operator' : None, 'travelerVersion' : ''}, 
        'runHarnessed' : {'operator' : None, 'travelerVersion' : ''}, 
        'defineHardwareType' : {'sequenceWidth' : 4, 'batchedFlag' : 0,
                                'subsystem' : 'Default', 'operator' : None},
        'registerHardware' : {'experimentSN' : '', 'manufacturerId' : '', 
                              'model' : '',
                              'manufactureDate' : '', 'manufacturer' : '',
                              'remarks' : '',
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
        'modifyHardwareLabel' : {'operator' : None, 'adding' : 'true',
                                 'reason' : 'Adjusted via API',
                                 'activityId' : None},
        'setHardwareLocation' : {'operator' : None, 'siteName' : None,
                                 'reason' : 'Adjusted via API', 
                                 'activityId' : None},
        'getHardwareHierarchy' : {'operator' : None, 'timestamp': None,
                                  'noBatched' : 'true'},
        'getContainingHardware' : {'timestamp' : None, 'operator' : None},
        'getManufacturerId' : {'operator' : None},
        'setManufacturerId' : {'reason' : 'Set via API', 'operator' : None},
        'getRunInfo' : {'operator' : None},
        'getRunResults' : {'function' : 'getRunResults', 'stepName' : None,
                           'schemaName' : None, 'filterKey' : None,
                           'filterValue' : None, 'operator' : None},
        'getRunFilepaths' : {'function' : 'getRunFilepaths', 'stepName' : None,
                             'operator' : None},
        'getResultsJH'  : {'function' : 'getResultsJH' , 
                           'schemaName' : None, 'model' : None,
                           'experimentSN' : None, 'filterKey' : None,
                           'filterValue' : None, 'hardwareLabels' : None,
                           'operator' : None},
        'getFilepathsJH'  : {'function' : 'getFilepathsJH' , 
                             'model' : None, 'experimentSN' : None,
                             'hardwareLabels' : None, 'operator' : None},
        'getManualRunResults' : {'function' : 'getManualRunResults',
                                 'stepName' : None, 'operator' : None},
        'getManualRunFilepaths' : {'function' : 'getManualRunFilepaths',
                                 'stepName' : None, 'operator' : None},
        'getManualRunSignatures' : {'function' : 'getManualRunSignatures',
                                    'stepName' : None,
                                    'activityStatus' : None,
                                    'operator' : None},
        'getManualResultsStep' : {'function' : 'getManualResultsStep',
                                  'model' : None, 'experimentSN' : None,
                                  'hardwareLabels' : None},
        'getManualFilepathsStep' : {'function' : 'getManualFilepathsStep',
                                    'model' : None, 'experimentSN' : None,
                                    'hardwareLabels' : None},
        'getManualSignaturesStep' : {'function' : 'getManualSignaturesStep',
                                     'model' : None, 'experimentSN' : None,
                                     'hardwareLabels' : None,
                                     'activityStatus' : None},
        'getActivity' : {'function' : 'getActivity',
                         'operator' : None},
        'getRunActivities' : {'function' : 'getRunActivities',
                              'operator' : None},
        'getRunSummary' : {'function' : 'getRunSummary',
                           'operator' : None},
        'getComponentRuns' : {'function' : 'getComponentRuns',
                              'travelerName' : None,
                              'operator' : None},
        'getHardwareInstances' : {'function' : 'getHardwareInstances',
                                  'experimentSN' : None, 'model' : None,
                                  'hardwareLabels' : None, 'operator' : None},
        }
        
        
    def __init__(self, operator=None, db='Prod', prodServer=True,
                 localServer=False, appSuffix='', cnfPath='~/.ssh/.etapi.cnf',
                 exp='LSST-CAMERA', debug=False):
        url = Connection.prodServerUrl + appSuffix
        if not prodServer: url = Connection.devServerUrl + appSuffix
        # localServer wins if set
        if localServer: url = Connection.localServerUrl + appSuffix
        # For now can't talk to CDMS databases
        #url += ('/exp/' + exp + '/')
        url += '/' + db + '/Results/'
        self.baseurl = url
        # if operator is None, prompt or use login?
        # do something for authorization
        self.operator = operator
        self.debug = debug
        self.env = dict(os.environ)
        self.db = db
        self.cnfPath = cnfPath
        if debug:
            print " baseurl is ", str(self.baseurl)
            print "Operator is ", str(self.operator)

    def __make_params(self, func, **kwds):
        '''
        Take keyword arguments and return dictionary suitable for use
        with func or raise ETClientAPIValueError.
        '''
        if func not in Connection.API:
            raise KeyError, 'eTraveler API does not support function %s' % str(func)
        cfg = dict(kwds)
        # function is a hidden parameter; don't want caller to set it
        if 'function' in cfg: del cfg['function']
        if not 'operator' in cfg:
            cfg['operator'] = None
        want = set(Connection.API[func])
        if ('cnfPath' in cfg) and (not 'cnfPath' in want):
            del cfg['cnfPath']
        if ('cnfPath' in want) and (not 'cnfPath' in cfg):
            cfg['cnfPath'] = self.cnfPath
        missing = want.difference(cfg)
        missingCopy = set(missing)
        for f in missing:
            if f in set(Connection.APIdefaults[func]) :
                cfg.update(f=Connection.APIdefaults[func][f])
                missingCopy.remove(f)
        if missingCopy:
            msg = 'Not given enough info to satisfy eTraveler API for %s: missing: %s' % (func, str(sorted(missingCopy)))
            #log.error(msg)
            raise ETClientAPIValueError, msg
        if 'cnfPath' in cfg:
            # get operator from the file
            cfg['operator'] = self.__readOperator(cfg['cnfPath'])
            del cfg['cnfPath']
            want -= set(['cnfPath'])
            
        if cfg['operator'] == None:
            if self.operator == None:
                raise ETClientAPIValueError, 'Missing parameter: must specify operator'
            cfg['operator'] = self.operator

        for k in want:
            if k not in cfg:
                cfg[k] = Connection.APIdefaults[func][k]
        query = {k:cfg[k] for k in want}
        return query

    def __make_query(self, command, func, **kwds):
        '''
        Make a query string for the given command and with the given
        keywords or raise ETClientAPIValueError.

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
            #print "For now, quit instead"
            #return
        try:
            r = requests.post(posturl, data = {"jsonObject" : jdata})
        except requests.HTTPError, msg:
            if self.debug:
                print "HTTPError: ", str(msg)
            raise
        except requests.RequestException, msg:
            if self.debug:
                print "Some other exception: ", str(msg)
            raise

        if self.debug:
            print 'No exceptions! '
            print "Status code: ", r.status_code
            print "Content type: ", r.headers['content-type']
            print "this is type of what I got: ", type(r)
            print "As text: ", r.text

        try:
            rsp = r.json()

            return rsp
        except ValueError, msg:
            # for now just reraise
            if self.debug:
                print "Unable to decode json"
                print "Original: ", str(r)
                print "Content type: ", r.headers['content-type']
                print "Text: ", r.text
                print "this is type of what I got: ", type(r)
            raise ETClientAPIValueError, msg

    def __readOperator(self, cnfpath):
        '''
        Use configuration file to determine value for operator.
        Used only for write operations.
        '''
        # Handle initial ~
        cnfExpanded = os.path.expanduser(cnfpath)
        
        # First check that file is sufficiently protected.  Only owner
        # should have access
        mode = os.stat(cnfExpanded).st_mode
        if (mode & (stat.S_IRWXG + stat.S_IRWXO)) != 0:
            raise ETClientAPIValueError, "Insufficiently protected config file"

        parser = ConfigParser.RawConfigParser()
        parser.read(cnfExpanded)
        writer = parser.get('eT API writer', self.db + '_writer')
        return writer
        
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
            raise ETClientAPIValueError, 'missing name parameter'

        # validate input
        badchars = ' $()/\\&<?'
        nm = k['name']
        for c in badchars:
            if c in nm:
                if c == ' ':
                    raise ETClientAPIValueError, 'No blanks allowed in hardware type name'
                else:
                    raise ETClientAPIValueError, 'name contains disallowed character %s' %c
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
            htype  - Required
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
        Returns: If success, id of new relationship type. Else raise exception
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
        Return: String 'Success' if operation succeeded, else raise exception
        '''
        k = dict(kwds)
        rqst = dict({})
        cmd = 'uploadYaml'
        rqst = self._reviseContents(k)

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
                    
        Return: String 'Success' if operation succeeded, else raise exception
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

    def setHardwareStatus(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN  identifier for component whose status will be set
           htype         hardware type of component
           status        new status to be set (e.g. READY, REJECTED, etc.)
           reason        defaults to 'Set by API'
           activityId    defaults to None
        Returns: String "Success" if operation succeeded, else raise exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'setHardwareStatus'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'setHardwareStatus', **rqst)
        return self._decodeResponse(cmd, rsp)

    def modifyHardwareLabel(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN  identifier for component whose status will be set
           htype         hardware type of component
           label         label name for label to be added or removed
           labelGroup    label group for label to be added or removed
           adding        'true' to add, 'false' for remove.  Default 'true'
           reason        defaults to 'Set by API'
           activityId    defaults to None
        Returns: String 'Success' if operation succeeded, else raise exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'modifyLabels'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'modifyHardwareLabel', **rqst)
        return self._decodeResponse(cmd, rsp)
        
    def adjustHardwareLabel(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN  identifier for component whose status will be set
           htype         hardware type of component
           label         label to be added or removed
           adding        'true' to add, 'false' for remove.  Default 'true'
           reason        defaults to 'Set by API'
           activityId    defaults to None
        Returns: String 'Success' if operation succeeded, else raise exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'setHardwareStatus'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'adjustHardwareLabel', **rqst)
        return self._decodeResponse(cmd, rsp)
    
    def setHardwareLocation(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN  identifier for component whose status will be set
           htype         hardware type of component
           locationName  new location for component
           siteName      new site for component.  Defaults to None (i.e.,
                         keep current site)
           reason        defaults to 'Set by API'
           activityId    defaults to None
        Returns: String "Success" if operation succeeded, else error msg
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'setHardwareLocation'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'setHardwareLocation', **rqst)
        return self._decodeResponse(cmd, rsp)

    def setManufacturerId(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN   identifier for component whose status will be set
           htype          hardware type of component
           manufacturerId new value
           reason         defaults to 'Set by API'
        Returns: String "Success" if operation succeeded, else error msg
        Operation will fail (raise ETClientAPIValueError exception) if old value 
        of manufacturer id in db wasn't empty string or blanks.
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'setManufacturerId'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'setManufacturerId', **rqst)
        return self._decodeResponse(cmd, rsp)

    def getManufacturerId(self, **kwds):
        '''
        Keyword Arguments:
           experimentSN   identifier for component whose status will be set
           htype          hardware type of component
        Returns: String value of manufacturer id if successful; else
                 raises exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'getManufacturerId'
        rqst = self._reviseCall(cmd, k)
        rsp = self.__make_query(cmd, 'getManufacturerId', **rqst)
        return self._decodeResponse(cmd, rsp)

    def getHardwareHierarchy(self, **kwds):
        '''
        Keyword Arguments:
            experimentSN  identifier for component for which subcomponent
                          information is to be returned
            htype         hardware type of the component
            noBatched     flag used for filtering output.  If true (default)
                          information about batched subcomponents will not
                          be returned
        Returns:
            If successful, array of dicts, each containing the following
            keys:
            level, parent_experimentSN, parent_hardwareTypeName, 
            child_experimentSN, child_hardwareTypeName, relationshipTypeName,
            slotName as well as (redundant and typically not of interest
            to clients) parent_id, child_id.
            If unsuccessful, raises exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'getHardwareHierarchy'
        rqst = self._reviseCall(cmd, k)
        #print 'getHardwareHierarchy called.  rqst parameters will be\n'
        #for r in rqst:
        #    print 'key %s, value %s'%(r, rqst[r])
        rsp = self.__make_query(cmd, 'getHardwareHierarchy', **rqst)
        return self._decodeResponse(cmd, rsp)

    def getContainingHardware(self, **kwds):
        '''
        Keyword Arguments:
            experimentSN  identifier for component for which containing
                          component information is to be returned
            htype         hardware type of the component
        Returns:
            If successful, array of dicts, each containing the following
            keys:
            level, parent_experimentSN, parent_hardwareTypeName, 
            child_experimentSN, child_hardwareTypeName, relationshipTypeName,
            slotName as well as (redundant and typically not of interest
            to clients) parent_id, child_id.
            If unsuccessful, raises exception
        '''
        k = dict(kwds)
        rqst = {}
        cmd = 'getContainingHardware'
        rqst = self._reviseCall(cmd, k)
        #print 'getHardwareHierarchy called.  rqst parameters will be\n'
        #for r in rqst:
        #    print 'key %s, value %s'%(r, rqst[r])
        rsp = self.__make_query(cmd, 'getContainingHardware', **rqst)
        return self._decodeResponse(cmd, rsp)

    def getRunInfo(self, **kwds):
        '''
        Keyword Arguements:
            activityId id of activity for which root activity id is requested
        Returns:  Dict if successful with keys 'rootActivityId' & 'runNumber'  
           Else raise ETClientAPIException
        '''
        cmd = 'getRunInfo'
        rsp = self.__make_query(cmd, cmd, **kwds)
        return self._decodeResponse(cmd, rsp)

    # The following are all subcommands of getResults.  Don't attempt
    # to do too much argument checking. Front end will handle it.
    def getRunResults(self, **kwds):
        '''
        Keyword Arguments:
           run - the only required argument
           stepName
           schemaName
           itemFilter (pair: key name and value)
        Return if successful:
           a dict.  Keys 'run', 'experimentSN' and 'hid' have scalar values
           Key 'steps'  has a dict as value.  
              Keys for the steps dict are step names
              Value for each key is a dict (call it the schemas dict)
                  Keys for the schemas dict are schema names
                  Value for each key is a list of schema instances
                     Each schema instance is a dict
                     Instance 0 is special: values of keys are type names

        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getRunResults', k)
        rsp = self.__make_query('getResults', 'getRunResults', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getResultsJH(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           travelerName -  required
           stepName - process step name, required
           schemaName - optional
           model - cut on hardware model; optional
           experimentSN - only fetch for this component; optional
           itemFilter (pair: key name and value)
           hardwareLabels - list of strings, each of form groupName:labelName
        '''
        k = dict(kwds)
        rqst = {}
        if 'hardwareLabels' in kwds:
            self.__validateLabels(kwds['hardwareLabels'])
        rqst = self._reviseCall('getResultsJH', k)
        rsp = self.__make_query('getResults', 'getResultsJH', **rqst);

        return self._decodeResponse('getResults', rsp)

    def getRunFilepaths(self, **kwds):
        '''
        Keyword Arguments:
           run - the only required argument
           stepname
        '''
        rsp = self.__make_query('getResults', 'getRunFilepaths', **kwds)
        return self._decodeResponse('getResults', rsp)

    def getFilepathsJH(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           travelerName -  required
           stepName - process step name, required
           model - cut on hardware model; optional
           experimentSN - only fetch for this component; optional
        '''
        k = dict(kwds)
        if 'hardwareLabels' in kwds:
            self.__validateLabels(kwds['hardwareLabels'])
        rqst = {}
        rqst = self._reviseCall('getFilepathsJH', k)
        rsp = self.__make_query('getResults', 'getFilepathsJH', **rqst);

        return self._decodeResponse('getResults', rsp)

    def getManualRunResults(self, **kwds):
        '''
        Keyword Arguments:
           run - the only required argument
           stepName
        Return if successful:
           a dict.  Keys 'runNumber', 'runInt', 'rootActivityId',
           'travelerName', 'travlerVersion', 'hardwareType', 'experimentSN', 
           'begin', 'end', 'subsystem', and 'runStatus' have scalar values
           Key 'steps'  has a dict as value.  
              Keys for the steps dict are step names
              Value for each key is a dict (call it the step dict)
                  Keys in the step dict are names (InputPattern.name)
                  Value for each key is another dict with keys
                    value, activityId, units and isOptional
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getManualRunResults', k)
        rsp = self.__make_query('getResults', 'getManualRunResults', **rqst)
        return self._decodeResponse('getResults', rsp)
    def getManualRunFilepaths(self, **kwds):
        '''
        Keyword Arguments:
           run - the only required argument
           stepName
        Return if successful:
           a dict.  Keys 'runNumber', 'runInt', 'rootActivityId',
           'travelerName', 'travlerVersion', 'hardwareType', 'experimentSN', 
           'begin', 'end', 'subsystem', and 'runStatus' have scalar values
           Key 'steps'  has a dict as value.  
              Keys for the steps dict are step names
              Value for each key is a dict (call it the step dict)
                  Keys in the step dict are names (InputPattern.name)
                  Value for each key is another dict with keys
                    virtualPath, catalogKey, activityId, isOptional

        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getManualRunFilepaths', k)
        rsp = self.__make_query('getResults', 'getManualRunFilepaths', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getManualRunSignatures(self, **kwds):
        '''
        Keyword Arguments:
           run - the only required argument
           stepName
        Return if successful:
           a dict.  Keys 'runNumber', 'runInt', 'rootActivityId',
           'travelerName', 'travlerVersion', 'hardwareType', 'experimentSN', 
           'begin', 'end', 'subsystem', and 'runStatus' have scalar values
           Key 'steps'  has a dict as value.  
              Keys for the steps dict are step names
              Value for each key is a dict (call it the step dict)
                  Keys in the step dict are names (InputPattern.name)
                  Value for each key is another dict with keys
                    value, activityId an units
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getManualRunSignatures', k)
        rsp = self.__make_query('getResults', 'getManualRunSignatures', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getManualResultsStep(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           travelerName -  required
           stepName - process step name, required
           model - cut on hardware model; optional
           experimentSN - only fetch for this component; optional
        '''
        k = dict(kwds)
        if 'hardwareLabels' in kwds:
            self.__validateLabels(kwds['hardwareLabels'])
        rqst = {}
        rqst = self._reviseCall('getManualResultsStep', k)
        rsp = self.__make_query('getResults', 'getManualResultsStep', **rqst);

        return self._decodeResponse('getResults', rsp)
        
    def getManualFilepathsStep(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           travelerName -  required
           stepName - process step name, required
           model - cut on hardware model; optional
           experimentSN - only fetch for this component; optional
        '''
        k = dict(kwds)
        if 'hardwareLabels' in kwds:
            self.__validateLabels(kwds['hardwareLabels'])
        rqst = {}
        rqst = self._reviseCall('getManualFilepathsStep', k)
        rsp = self.__make_query('getResults', 'getManualFilepathsStep', **rqst);

        return self._decodeResponse('getResults', rsp)

    def getManualSignaturesStep(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           travelerName -  required
           stepName - process step name, required
           model - cut on hardware model; optional
           experimentSN - only fetch for this component; optional
        '''
        k = dict(kwds)
        if 'hardwareLabels' in kwds:
            self.__validateLabels(kwds['hardwareLabels'])
        rqst = {}
        rqst = self._reviseCall('getManualSignaturesStep', k)
        rsp= self.__make_query('getResults', 'getManualSignaturesStep', **rqst);

        return self._decodeResponse('getResults', rsp)

    
    def getActivity(self, **kwds):
        '''
        Keyword arguments:
          activityId (required).
        Returns:
          dict of attributes belonging to the activity including
          id, stepName, beginning and ending timestamps and status
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getActivity', k)
        rsp = self.__make_query('getResults', 'getActivity', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getRunActivities(self, **kwds):
        '''
        Keyword arguments:
          run (required).
        Returns:
          list of dicts, one for each activity in the run. Keys in each
          dict are the same as for return from getActivity
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getRunActivities', k)
        rsp = self.__make_query('getResults', 'getRunActivities', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getRunSummary(self, **kwds):
        '''
        Keyword arguments:
          run (required).
        Returns:
          dict of attributes belonging to the run, including
          hardware type and experimentSN for component
          traveler name
          traveler version
          run number as string and int
          root activity id
          subsystem
          run status
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getRunSummary', k)
        rsp = self.__make_query('getResults', 'getRunSummary', **rqst)
        return self._decodeResponse('getResults', rsp)

    def getComponentRuns(self, **kwds):
        '''
        Keyword Arguments:
           htype - hardware type name, required
           experimentSN - component identifier, required
        Returns:
           for each traveler execution (run) on the component, return
           a dict of information, similar to return from getRunSummary
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getComponentRuns', k)
        rsp = self.__make_query('getResults', 'getComponentRuns', **rqst)
        return self._decodeResponse('getResults', rsp)
 
    def getHardwareInstances(self, **kwds):
        '''
        Keyword Arguments:
           htype        - Hardware type name. The only required argument
           experimentSN - If supplied, data for only this instance  will be
                          returned
        Return if successful:
           a list of dicts, one per hardware instance.  
           Keys for each dict are
           experimentSN, model, manufacturer, manufacturer id, 
           remarks (string which may be optionally entered when component
           is registered) and status
        '''
        k = dict(kwds)
        rqst = {}
        rqst = self._reviseCall('getHardwareInstances', k)
        rsp = self.__make_query('getResults', 'getHardwareInstances', **rqst)
        return self._decodeResponse('getResults', rsp)
 
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
            raise ETClientAPIValueError, 'Missing slotName argument'

        slist = k['slotNames']

        if isinstance(slist, str): slist = [slist]

        if not isinstance(slist, list):
            raise ETClientAPIValueError, 'Improper slotName list'
        for e in slist: 
            if not isinstance(e, str):
                raise ETClientAPIValueError, 'Slot names must be strings'
            if ',' in e:
                raise ETClientAPIValueError, 'Slot names may not contain commas'

        if (len(slist) != 1) and (len(slist) != num):
            raise ETClientAPIValueError, 'Wrong number of slotnames'

        kwds['slotNames'] = string.join(slist, ',')
        return kwds
    
    def __validateLabels(self,labels):
        if type(labels) == type("a"):
            self.__validateLabel(labels)
        else:
            if type(labels) == type([]):
                for label in labels:
                    self.__validateLabel(label)
            else:
                raise ETClientAPIValueError, 'Invalid labels list'

    def __validateLabel(self,label):
        # check for spaces
        if ' ' in label:
            raise ETClientAPIValueError('Label "' + label + '" contains a space')
        parts = label.split(':')
        if len(parts) == 2:
            if len(parts[0]) != 0:
                return
        raise ETClientAPIValueError('Label "' + label + '" improperly formed')


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
            raise ETClientAPIValueError, 'No input yaml. Use contents or filepath keyword'
        return k

    def _reviseCall(self, cmd, k):
        if cmd == 'setHardwareStatus':
            if 'htype' not in k: raise ETClientAPIValueError, 'Missing htype parameter'
            k['hardwareTypeName'] = k['htype']
            del k['htype']
            if 'label' in k:
                k['hardwareStatusName'] = k['label']
                del k['label']
            elif 'status' in k:
                k['hardwareStatusName'] = k['status']
                del k['status']
            else:
                raise ETClientAPIValueError, 'Missing label or status argument'
        elif cmd in ['setHardwareLocation', 'getHardwareHierarchy',
                     'getContainingHardware', 'getManufacturerId',
                     'setManufacturerId', 'modifyLabels']:
            if 'htype' not in k:
                raise ETClientAPIValueError, 'Missing htype parameter'
            k['hardwareTypeName'] = k['htype']
            del k['htype']
        elif cmd in ['getResultsJH', 'getFilepathsJH', 'getManualResultsStep',
                     'getManualFilepathsStep', 'getManualSignaturesStep',
                     'getHardwareInstances', 'getComponentRuns']:
            if 'hardwareType' not in k:
                if 'htype' not in k:
                    raise ETClientAPIValueError, 'Missing hytpe parameter'
                k['hardwareType'] = k['htype']
                del k['htype']
            if 'hardwareLabels' in k:
                if type(k['hardwareLabels']) == type('a'):
                    l = [k['hardwareLabels'] ]
                    k['hardwareLabels'] = l
        if cmd == 'modifyLabels':
            if 'label' not in k:
                raise ETClientAPIValueError, 'Missing label parameter'
            if 'group' not in k:
                raise ETClientAPIValueError, 'Missing group parameter'
            k['labelName'] = k['label']
            k['labelGroupName'] = k['group']
            del k['label']
            del k['group']
        if cmd in ['getRunResults', 'getResultsJH']:
            if 'itemFilter' in k:
                filt = k['itemFilter']
                #print 'itemFilter is ', filt
                self._parseItemFilter(filt)
                k['filterKey'] = filt[0]
                k['filterValue'] = filt[1]
                del k['itemFilter']
        if cmd in ['getHardwareHierarchy', 'getContainingHardware']:
            if 'timestamp' in k:
                k['timestamp'] = self._makeIsoTime(k['timestamp'])
        if cmd == 'getActivity':
            if 'activityId' in k:
                k['activityId'] = str(k['activityId'])
            else:
                raise ETClientAPIValueError, 'Missing activityId argument'

        if cmd in ['getRunActivities', 'getRunResults', 'getRunFilepaths',
                   'getRunSummary', 'getManualRunResults',
                   'getManualRunFilepaths', 'getManualRunSignatures']:
            if 'run' in k:
                k['run'] = str(k['run'])
            else:
                raise ETClientAPIValueError, 'Missing run argument'
        return k

    def _parseItemFilter(self, itemFilter):
        if not isinstance(itemFilter, tuple):
            raise KeyError, 'itemFilter must be tuple'
        if not len(itemFilter) == 2:
            raise KeyError, 'itemFilter must be tuple of length 2'
        if not isinstance(itemFilter[0], str): 
            raise KeyError, 'itemFilter key must be a string'
        if isinstance(itemFilter[1], str) or isinstance(itemFilter[1], int) or isinstance(itemFilter[1], long): return
        raise KeyError, 'itemFilter value must be integer or string'

    def _makeIsoTime(self, inputTime):
        try:
            isotime = parsetime(inputTime).isoformat()
        except ValueError,msg:
            raise ETClientAPIValueError("Bad time string. " + str(msg))

        return isotime

    def _decodeResponse(self, command, rsp):
        '''
        Common error handling for response to query. If good response,
        differentiate by command issued
        '''
        if type(rsp) is dict:
            if rsp['acknowledge'] == None:
                if (command == 'runAutomatable'): return rsp['command']
                elif (command in ['uploadYaml', 'setHardwareStatus',
                                  'modifyLabels', 'setHardwareLocation', 
                                  'setManufacturerId']):
                    return 'Success'
                elif (command in ['getHardwareHierarchy', 
                                  'getContainingHardware']):
                    return rsp['hierarchy']
                elif (command == 'getManufacturerId'):
                    if rsp['manufacturerId'] is None: return ""
                    else: return rsp['manufacturerId']
                elif (command == 'getRunInfo'):
                    return {'rootActivityId' : rsp['rootActivityId'],
                            'runNumber' : rsp['runNumber']}
                elif (command == 'getResults'):
                    return rsp['results']
                else: return rsp['id']
            else:
                if ((command == 'setManufacturerId') and ('already set' in rsp['acknowledge'] ) ):
                    raise ETClientAPIValueError, rsp['acknowledge']
                elif 'No data found' in rsp['acknowledge']:
                    raise ETClientAPINoDataException, rsp['acknowledge']
                else:
                    raise ETClientAPIException, rsp['acknowledge']
        else:
            if self.debug:
                print 'return value of unexpected type', type(rsp)
                print 'return value cast to string is: ', str(rsp)
            raise ETClientAPIException, str(rsp)
