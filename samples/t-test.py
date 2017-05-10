#!/usr/bin/env python

from pyVmomi import vim
from prometheus_client import start_http_server, Summary, Counter, Gauge
from tools import cli
from pyVim.connect import SmartConnect, Disconnect
import atexit
#import getpass
import ssl
import datetime

def main():

    args = cli.get_args()

    # Start up the server to expose the metrics.
    start_http_server(8000)

    # define a gauge
    g = Gauge('vmwaresamplegauge', 'vmware sample gauge', ['name'])

    # Connect to the host without SSL signing
    try:
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
    print('Start: Date now: %s' % datetime.datetime.now())
    counterInfo = {}
    counterids=perfManager.QueryPerfCounterByLevel(level=1)

    for c in counterids:
        fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
        counterInfo[fullName] = c.key

    print('QueryPerfCounterByLevel: Date now: %s' % datetime.datetime.now())
    collected=[ 'cpu.usage.average', 'cpu.usagemhz.average', 'cpu.ready.summation', 'mem.usage.average', 'mem.swapinRate.average', 'mem.swapoutRate.average', 'mem.vmmemctl.average', 'mem.consumed.average', 'mem.overhead.average', 'disk.usage.average'  ]
    counterIDs = [counterInfo[k] for k in collected if k in counterInfo]

##############################################################################
    # create a list of vim.VirtualMachine objects so that we can query them for statistics
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True

# REQUEST CreateContainerView
    containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)

    children = containerView.view
    count_vms=len(children)
    print("Count of VMs:" + str(count_vms))
    print('CreateContainerView: Start: Date now: %s' % datetime.datetime.now())

# REQUEST MetricId
#    metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
#                                                   instance="*")
#                  for c in counterIDs]
#    print('MetricId: Start: Date now: %s' % datetime.datetime.now())
########################################################################################
    for child in children:
     if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
        lis=child.summary.config.annotation.split('\n')
        d = dict(s.rsplit(':',1) for s in filter(None, lis))

# REQUEST MetricID
        metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
                                                     instance="*")
                     for c in counterIDs]
        print('MetricId: Start: Date now: %s' % datetime.datetime.now())

#        print(metricIDs)
# REQUEST QuerySpec
        spec = vim.PerformanceManager.QuerySpec(maxSample=1,
                                                entity=child,
                                                metricId=metricIDs,
                                                intervalId=20)

        print('QuerySpec: Start: Date now: %s' % datetime.datetime.now())
# REQUEST QueryStats
        result = perfManager.QueryStats(querySpec=[spec])
        print('QueryStats: Start: Date now: %s' % datetime.datetime.now())
        # Loop through the results and print the output
        output = ""
        for r in result:
            if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
               for val in result[0].value:
                    if val:
                        output += "id:" + child.summary.config.name + ","
                        output += counterInfo.keys()[
                                  counterInfo.values().index(val.id.counterId)]
                        output += ": " + str(val.value[0]) + ", name:" + d['name'] + ", project_id:" + d['projectid'] + "\n"
#               output += "\n"

        print(filter(None, output))

        if counterInfo.keys()[counterInfo.values().index(val.id.counterId)] == 'cpu.usage.average':
            g.labels(d['name']).set(val.value[0])

if __name__ == "__main__":
    main()
