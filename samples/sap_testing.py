#!/usr/bin/env python
"""
 Written by Lance Hasson
 Github: https://github.com/JLHasson

 Script to report all available realtime performance metrics from a
 virtual machine. Based on a Java example available in the VIM API 6.0
 documentationavailable online at:
 https://pubs.vmware.com/vsphere-60/index.jsp?topic=%2Fcom.vmware.wssdk.pg.
 doc%2FPG_Performance.18.4.html&path=7_1_0_1_15_2_4

 Requirements:
     VM tools must be installed on all virtual machines.
"""

from pyVmomi import vim
from tools import cli
from pyVim.connect import SmartConnect, Disconnect
import atexit
import getpass
import ssl

def main():

    args = cli.get_args()

    # Connect to the host without SSL signing
    try:
#        si = SmartConnectNoSSL(
#            host=args.host,
#            user=args.user,
#            pwd=args.password,
#            port=int(args.port))
#        atexit.register(Disconnect, si)

        context = ssl._create_unverified_context()
        si = SmartConnect(host=args.host,
             user=args.user,
             pwd=args.password,
             port=int(args.port),
             sslContext=context)

    except IOError as e:
        pass

    if not si:
        raise SystemExit("Unable to connect to host with supplied info.")

    content = si.RetrieveContent()
    perfManager = content.perfManager


##############################################################################
    # create a mapping from performance stats to their counterIDs
    # counterInfo: [performance stat => counterId]
    # performance stat example: cpu.usagemhz.LATEST
    # counterId example: 6
#    counterInfo = {}
#    for c in perfManager.perfCounter:
#        prefix = c.groupInfo.key
#        fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
#        print(fullName)
#        counterInfo[fullName] = c.key

##############################################################################
    # create a list of vim.VirtualMachine objects so
    # that we can query them for statistics
 #   container = content.rootFolder
 #   viewType = [vim.VirtualMachine]
 #   recursive = True

 #   print("Getting all VMs ...")
 #   containerView = content.viewManager.CreateContainerView(container,
 #                                                           viewType,
 #                                                           recursive)

  #  print(containerView)
  #  children = containerView.view
  #  print(children)

    counterids=perfManager.QueryPerfCounterByLevel(level=1)

    metricids={}

    for r in counterids:
      counteridkey = r.groupInfo.key + "." + r.nameInfo.key + "." + r.rollupType
      metricids[counteridkey] = r.key

    print(counteridkey)
    liste=[ 'cpu.totalmhz.average', 'cpu.usagemhz.average', 'cpu.ready.summation' ]
    CounterIDs = [metricids[k] for k in liste if k in metricids]



if __name__ == "__main__":
    main()