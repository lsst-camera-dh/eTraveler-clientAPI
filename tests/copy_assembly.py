#!/usr/bin/env python
from __future__ import print_function
import sys
import argparse
import os

from  eTraveler.clientAPI.connection import Connection, ETClientAPINoDataException

class CopyAssembly:
    def __init__(self, args):
        '''
        Verify and store information passed in command-line argumens
        '''
        self.lsst_id = None
        self.site = None
        self.loc  = None
        self.conn = None
        self.args = args

        # Must of one of lsstId, number arguments
        if args.lsst_id is not None:
            self.lsst_id = args.lsst_id
        elif args.cmpnt_num is not None:
            self.lsst_id = ''.join([args.htype,'-', args.cmpnt_num])
        else:
            raise NameError('Neither lsstId nor number supplied') 

        # if --location option was used, check it has proper syntax
        if (args.siteloc) is not None:
            try:
                self.site,self.loc = (args.siteloc).split(':')
            except:
                print('--location argument of improper form')
                raise


        
    def formList(self, response, good_types):
        '''
        response is the response from the getHierarchy query
        good_types are the hardware types of interest
        
        Returns a list of dicts, each containing information to be used
        in registering one component
        '''
        outlist = []
        didRoot = False
        print('Good types are ')
        for g in good_types: print(g)
        for r in response:
            chtype = r['child_hardwareTypeName']
            if chtype not in good_types:
                print(chtype, ' not in list of hardware types')
                continue
            if r['level'] == '0':
                if not didRoot:
                    dict0 = {}
                    dict0['level'] = 0
                    dict0['found'] = False
                    phtype = r['parent_hardwareTypeName']
                    pexpSN = r['parent_experimentSN']
                    dict0['htype'] = phtype
                    dict0['leaf'] = False
                    try:
                        rootInfos=self.conn.getHardwareInstances(htype=phtype, experimentSN=pexpSN)
                        rootInfo = rootInfos[0]
                        for k in rootInfo: dict0[k] = rootInfo[k]
                        outlist.append(dict0)
                        didRoot = True
                        print("Appended to outlist")
                    except:
                        raise

            print('processing type ', chtype)
            cdict = {}
            cdict['parent'] = r['parent_experimentSN']
            cdict['slotName'] = r['slotName']
            cdict['relationshipName'] = r['relationshipTypeName']
            cdict['level'] = int(r['level']) + 1
            cdict['htype'] = chtype
            cdict['leaf'] = True    #   default assumption
            cexpSN = r['child_experimentSN']
            try:
                infos = self.conn.getHardwareInstances(htype=chtype, 
                                                       experimentSN=cexpSN)
                info = infos[0]
                for k in info: cdict[k] = info[k]
                outlist.append(cdict)
                print("Appended to outlist")
            except:
                raise

        print('len of out list is ', len(outlist))
        for cdict in outlist:
            for r in response:
                if r['parent_experimentSN'] == cdict['experimentSN'] and r['parent_hardwareTypeName'] == cdict['htype']:
                    cdict['leaf'] = False
        return outlist

    def register(self, elt):
        if self.site is None:
            site, location = elt['location'].split(':')
        else:
            site = self.site
            location = self.loc

        newId =self.conn.registerHardware(htype=elt['htype'],site=site,
                                          location=location,
                                          experimentSN=elt['experimentSN'],
                                          manufacturerId=elt['manufacturerId'],
                                          manufacturer=elt['manufacturer'],
                                          model=elt['model'])

    def setReady(self, elt, forReal):
        if forReal:
            self.conn.setHardwareStatus(experimentSN=elt['experimentSN'],
                                        htype=elt['htype'], status='READY',
                                        reason='Set by copy_assembly')
            print('Set status to READY for component ', elt['experimentSN'])
        else:
            print('Would have set status to READY for component ',
                  elt['experimentSN'])

    def execute(self):
        source_list = []
        args = self.args
        
        uname = args.u
        if uname is None:
            uname = os.getenv('USER')

        source_db = self.args.source_db
        print('Connecting to database ', source_db)
        self.conn = Connection(uname, source_db,prodServer=True,
                               debug=False)
    
        rsp = []
        
        try:
            print("Results from getHardwareHierarchy unfiltered:")
            iDict = 0
            rsp = self.conn.getHardwareHierarchy(experimentSN=self.lsst_id,
                                                 htype=args.htype,
                                                 noBatched='true')

            source_list=self.formList(rsp, args.child_types)
            print('#Components found is ', len(source_list))

            for elt in source_list:
                print('An element: ', elt['experimentSN'], 
                      elt['manufacturerId'])
                if elt['level'] > 0:
                    print('     ', elt['parent'], elt['slotName'])
                    
        except Exception as msg:
            print('Query of source db failed with exception: ')
            print(msg)
            sys.exit(1)

### Stuff to be properly indented

        # Make new connection to dest db
        print('Connecting to database ', args.dest_db)
        forReal = args.forreal
        if args.forreal:
            print('Continue for real? Y or N?')
            try:
                ans = raw_input('--> ')
            except NameError:
                ans = input('-->  ')

            if ans[0] != 'Y':
                print('Switching to dry-run behavior')
                forReal = False

        self.conn = Connection(uname, args.dest_db,prodServer=True,debug=False)

# SHOULD check that hardware types exist, but for now just hope for the best 
# Query will fail 
#  we get the wrong answer.)

# Query dest db to find out which ones exist; create any that don't
# For now do this one by one.  Could instead make 1 query per htype

        for elt in source_list:
            print('Working on component ', elt['experimentSN'])
            #print('Value for key leaf is: ', elt['leaf'])
            try:
                rs = self.conn.getHardwareInstances(htype=elt['htype'],
                                                    experimentSN=elt['experimentSN'])
                print('Component found in dest db. No register action')
            except ETClientAPINoDataException:
                print('Did not find corresponding component in dest db')
                if (forReal):
                    self.register(elt)
                else:
                    print('Dryrun.  No attempt to create entry')
                pass
            except:
                raise

            if elt['leaf'] is True:
                self.setReady(elt, forReal)
        

if __name__=='__main__':

    desc='Copy components and subcomponents of interest from one db to another'
    ep='''One of --lsstId and --number must be specified.  --lsstId takes
      precedence. 
      For hardware types other than LCA-11021_RTM the default child
      component list is all non-batched types
   ''' 
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=ep)

    parser.add_argument('-s', '--source', default='Prod', 
                        dest='source_db', help='Source database')
                        
    parser.add_argument('--dest', default='Dev', 
                        dest='dest_db', help='Destination database')
    parser.add_argument('--hardwareType',
                        default='LCA-11021_RTM', dest='htype', 
                        help='Hardware type of top component')
    parser.add_argument('--lsstId', help='Full lsst id of top component',
                        dest='lsst_id')
    parser.add_argument('--number', dest='cmpnt_num',
                        help='Cmpnt number. Append to hardware type to form lsstId')
    parser.add_argument('--children', dest='child_types', 
                        default=['LCA-10753_RSA','LCA-13574', 'e2v-CCD', 
                                 'ITL-CCD'],
                        help='List of non-batch child types to duplicate. Use ["*"] for all')
    parser.add_argument('--dryrun', dest='forreal', action='store_false',
                        help='Write actions are displayed only. Store in forreal variable')
    parser.add_argument('--forreal', dest='forreal', action='store_true',
                        help='Really do it')
    parser.add_argument('--user', dest='u', default=None, 
                    help='username to use for queries. Defaults to login name')
    parser.add_argument('--location', dest='siteloc', default=None,
                        help='New components will be located here. Must be of form sitename:place-in-site. If not supplied, location will be copied from source database. In either case script will halt with failure if location does not exist in destination db')
    parser.set_defaults(forreal=False)
    args = parser.parse_args()

    print('args:  ', args)

    ca = CopyAssembly(args)

    ca.execute( )
    
    sys.exit(0)


