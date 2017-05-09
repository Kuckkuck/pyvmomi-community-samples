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
        atexit.register(Disconnect, si)

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
  #  counterInfo = {}
  #  for c in perfManager.perfCounter:
  #      fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
  #      print(fullName)
  #      counterInfo[fullName] = c.key
#    counterids=perfManager.QueryPerfCounterByLevel(level=1)


#    for c in perfManager.QueryPerfCounterByLevel(level=1):
#      fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
#      counterInfo[fullName] = c.key

#    print(counterInfo)
#    liste=[ 'cpu.usage.average', 'cpu.usagemhz.average', 'cpu.ready.summation', 'mem.usage.average', 'mem.swapinRate.average', 'mem.swapoutRate.average', 'mem.vmmemctl.average', 'mem.consumed.average', 'mem.overhead.average', 'disk.usage.average'  ]
#    counterIDs = [counterInfo[k] for k in liste if k in counterInfo]
#    print(counterIDs)

##############################################################################
    # create a list of vim.VirtualMachine objects so
    # that we can query them for statistics
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True

    containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)

    children = containerView.view
#    print(children)

    for child in children:
     if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
        lis=child.summary.config.annotation.split('\n')
#        print("simple list ", lis)
#        print("reversed list ",  reversed(lis))
#        print("enumerated list ", enumerate(reversed(lis)))
        d = dict(s.rsplit(':',1) for s in filter(None, lis))
        print(d)

##############################################################################

    # Loop through all the VMs
 #   for child in children:
        # Get all available metric IDs for this VM
#        counterIDs = [m.counterId for m in
#                      perfManager.QueryAvailablePerfMetric(entity=child)]
#        counterIDs = [ 6, 12 ]


#        perfinfo = [vim.PerformanceManager.CounterInfo(key=i)
#        for i in counterIDs]
#        print(perfinfo)


#        print(counterIDs)
        # Using the IDs form a list of MetricId
        # objects for building the Query Spec
 #       metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
 #                                                    instance="*")
 #                    for c in counterIDs]

 #       print(metricIDs)

        # Build the specification to be used
        # for querying the performance manager
 #       spec = vim.PerformanceManager.QuerySpec(maxSample=1,
 #                                               entity=child,
 #                                               metricId=metricIDs)
#                                                intervalId=10)

        # Query the performance manager
        # based on the metrics created above
#        result = perfManager.QueryStats(querySpec=[spec])
#        print(result)

        # Loop through the results and print the output
#        output = ""
#        for r in result:
#            print(r)
#            if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
#               output += "id:" + child.summary.config.name + "\n" + child.summary.config.annotation
#               for val in result[0].value:
#                  output += counterInfo.keys()[
#                            counterInfo.values().index(val.id.counterId)]
#                  output += ": " + str(val.value[0]) + "," + child.summary.config.annotation.name + "\n"
#               output += "\n"

#        print(output)

if __name__ == "__main__":
    main()

