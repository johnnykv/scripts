import gevent
import gevent.monkey

gevent.monkey.patch_all()  # NOQA

import sqlite3

from heralding.reporting.file_logger import FileLogger
from heralding.misc.common import on_unhandled_greenlet_exception

from heralding.reporting.reporting_relay import ReportingRelay



# Reconstructs the heraldinv CSV file from a sqlite db

if __name__ == '__main__':

    reportingRelay = ReportingRelay()
    reportingRelay.start()

    logFile = 'exported_heralding_activity.log'
    greenlet = FileLogger(logFile)
    greenlet.link_exception(on_unhandled_greenlet_exception)
    greenlet.start()
    greenlet.Ready.wait()

    conn = sqlite3.connect('heralding.db')
    conn.text_factory = str
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = 'SELECT * from auth'
    for row in cursor.execute(query):
        ReportingRelay.queueLogData(dict(row))
        gevent.sleep()

    print ReportingRelay.getQueueSize()
    # tell relay to shut down when finished sending messages
    reportingRelay.stop()
    print ReportingRelay.getQueueSize()
    gevent.wait([reportingRelay,greenlet])
