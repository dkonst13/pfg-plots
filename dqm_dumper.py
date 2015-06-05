#!/usr/bin/env python
"""PFG analysis helper.
"""

# python-2 compatibility
from __future__ import division        # 1/2 = 0.5, not 0
from __future__ import print_function  # print() syntax from python-3

import os
import sys
import subprocess
import ROOT

def main():
    """Steering function.
    """
    # template path to DQM files
    pathfmt = 'https://cmsweb.cern.ch/dqm/online/data/browse/ROOT/{0:05d}xxxx/{1:07d}xx/DQM_V0001_{3}_R{2:09d}.root'

    # read input / print usage info
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print('Usage: {0} <run_number>'.format(sys.argv[0]))
        sys.exit(1)

    # run number to process
    run = int(sys.argv[1])

    # create output directories
    for d in ['downloads', 'plots']:
        if not os.access(d, os.X_OK):
            os.mkdir(d)

    # download Ecal root file
    url = pathfmt.format(int(run/10000), int(run/100), run, 'Ecal')
    path = os.path.join('downloads', os.path.basename(url))
    download(url, path)

def download(url, localpath):
    """Downloads file with wget.

    File is first downloaded under a name 'tmpfile' and then renamed: the
    renaming operation is atomic, so the file is either fully downloaded or not
    downloaded at all.
    """
    if os.access(localpath, os.R_OK):
        return  # file already downloaded

    tmpfile = os.path.join(os.path.dirname(localpath), 'tmpfile')

    keypath  = os.path.join(os.getenv('HOME'), '.globus/userkey.pem')
    certpath = os.path.join(os.getenv('HOME'), '.globus/usercert.pem')

    # run wget
    ret = subprocess.call(['wget', '-q', '--no-check-certificate',
                           '--certificate=' + certpath,
                           '--private-key=' + keypath, url, '-O', tmpfile],
                          stdout=sys.stdout, stderr=sys.stderr)
    if ret != 0:
        sys.exit(1)

    # atomic rename
    os.rename(tmpfile, localpath)

if __name__ == '__main__':
    main()
