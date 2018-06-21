#!/usr/bin/env python
from __future__ import print_function
import sys
import csv
import codecs

from  eTraveler.clientAPI.connection import Connection
from  eTraveler.clientAPI.connection import ETClientAPINoDataException

def get_NCRs(conn, htype='LCA-11021_RTM', component='LCA-11021_RTM-004'):
    rsp = {}
    url_base = 'https://lsst-camera.slac.stanford.edu/eTraveler/exp/LSST-CAMERA/displayActivity.jsp?dataSourceMode=prod&activityId='
    try:
        labels = ['Priority:', 'Mistake:']
        print("Calling getHardwareInstances for hardware type ", htype, " one label") 

        rsp = conn.getHardwareNCRs(htype=htype, experimentSN=component,
                                   items='children',ncrLabels=labels)
        print("Returned list of NCRs for component ", component)
        entry = 0
        # Also write to CSV file
        with open(component + '.csv', 'w') as csvfile:
            fieldnames = ['entry', 'level', 'hardwareType', 'experimentSN',
                          'NCRname', 'NCRnumber', 'NCRurl','currentStep',
                          'NCRstatus', 'ncrLabels', 'runNumber', 'done', 
                          'should_see', 'did_see']
            #, 'NCRtype', 'disposition']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for h in rsp:
                print("\nfor entry ",entry, " NCR# ", h['NCRnumber'])
                for k in h:
                    print('Value for key ', k, ' is ',h[k])
                    
                h['entry'] = entry
                h['NCRurl'] = url_base + str(h['NCRnumber'])
                del h['exceptionId']
                del h['hardwareId']
                runrsp = conn.getManualRunResults(run=h['runNumber'])
                steps = runrsp['steps']
                for s in steps: print(s)
                
                # The remaining fields only get filled in if the NCR was far enough along
                h['should_see'] = 'N/A'
                h['did_see'] = 'N/A'
                #h['NCRtype'] = 'N/A'
                #h['disposition'] = 'N/A'
                if 'NCR_A_Description' in steps:
                    descr = steps['NCR_A_Description']
                    h['should_see'] = descr['Should_have_been_seen']['value']
                    h['did_see'] = descr['Was_seen']['value']

                    if type(h['should_see']) != type(""):
                        #print("Offending text: ")
                        #print(h['should_see'])

                        try:
                            h['should_see'] = h['should_see'].encode('ascii', errors='replace')
                        except:
                            h['should_see'] = '(ascii encoding error)'

                    if type(h['did_see']) != type(""):
                        #print("Offending text: ")
                        #print(h['did_see'])
                        
                        try:
                            h['did_see'] = h['did_see'].encode('ascii', errors='replace')
                        except:
                            h['did_see'] = '(ascii encoding error)'
                                
                    
                    #if 'NCR_Simple' in steps: 
                    #    h['NCRtype'] = 'Simple'
                    #    h['disposition'] = steps['NCR_Simple']['Provide_the_disposition']['value']

                    #if 'NCR_C_Final_disposition' in steps:
                    #    h['disposition'] = steps['NCR_C_Final_disposition']['Final_disposition']['value']
                    #    h['NCRtype'] = 'Complex'

                    
                writer.writerow(h)
                entry +=1


        sys.exit(0)
    except ETClientAPINoDataException as msg:
        print('No data exception: ',msg)
        sys.exit(1)
    except Exception as msg:
        print('Operation failed with exception: ')
        print(msg)
        sys.exit(1)
         
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="""
        Generate csv of NCR info for specified component
    """)
    parser.add_argument('--component','-c',  help='experimentSN',
                        default='LCA-11021_RTM-004')
    parser.add_argument('--htype', '-ht', help='hardware type',
                        default='LCA-11021_RTM')
    myConn = Connection('jrb', 'Prod', debug=False, prodServer=True, 
                        appSuffix='')
    args = parser.parse_args()
    #get_NCRs(myConn, component='LCA-11021_RTM-005')
    print("Arguments:")
    adict = vars(args)
    print(adict)
    get_NCRs(myConn, htype=adict['htype'], component=adict['component'])
