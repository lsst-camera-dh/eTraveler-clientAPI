#!/usr/bin/env python
'''
Sample user script for eTraveler API
'''

import os
import eTravelerClient.connection

# Assume top-level directory is in an environment variable
topdir = os.environ.get('DATADIR')
if not topdir:
    raise RuntimeError, 'cannot determine top-level data directory'

# Save list of subdirectories. Their names are the manufacturer id's
# of the components to be processed
manIds = list(os.listdir(topdir))

# Connect to eTraveler (prod) server with intent to use Dev database
conn = eTravelerClient.connection.Connection('jrb', 'Dev')
if not conn:
    raise RuntimeError, 'unable to authenticate'

for manId in manIds:
    # maybe some sort of sanity check that cmp is of a particular form?

    # can also specify model, manufacture date
    hid = conn.registerHardware('ASPIC', 'Orsay', 'Storage cabinet',
                                experimentSN='LSST-'+str(manId),
                                manufactureId=manId)

    # Run a traveler containing one or more harnessed jobs
    # The job(s) will be able to find the associated data from the
    # environment variables DATADIR and LCATR_UNIT_ID.  The value
    # of the latter is the same string set into experimentSN above
    status = connection.runTraveler(hid, 'ASPIC_data_ingest', 'active',
                                    'ASPIC')


