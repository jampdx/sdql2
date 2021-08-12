
# Robust WSGI auto-reloading for development.
#
# Reload a WSGI application on source change. Keep the old code alive
# when the change has syntax errors.
# Never close the socket, never refuse a connection.

import os
import sys
import logging.config
import time
import threading
import ConfigParser
from Queue import Empty

from multiprocessing import Process, Queue, Event
from multiprocessing import active_children
from optparse import OptionParser
from wsgiref.simple_server import make_server

import paste.deploy
import paste.reloader

POLL_INTERVAL = 15   # check for changes every n seconds.
SPINUP_TIME = 300    # application must start within this time.

class Monitor(paste.reloader.Monitor):
    def __init__(self, tx=None, rx=None, check_files=[]):
        paste.reloader.Monitor.__init__(self, POLL_INTERVAL)
        self.state = 'RUN'
        self.tx = tx
        self.rx = rx
        #print "Monitor setting check files:",check_files
        self.check_files = check_files
        
    def check_reload(self):
        for filename in self.check_files:
            try:
                stat = os.stat(filename)
                if stat:
                    mtime = stat.st_mtime
                else:
                    mtime = 0
            except (OSError, IOError):
                continue
            #if not self.module_mtimes.has_key(filename):
            #    self.module_mtimes[filename] = mtime
            #elif self.module_mtimes[filename] < mtime:
            if self.module_mtimes.setdefault(filename,mtime) < mtime:
                print >> sys.stderr, (
                    "%s changed; reloading..." % filename)
                return False
        return True
    
    def periodic_reload(self):

        while not self.rx.is_set():
            if not self.check_reload():
                self.state = 'STANDBY'
                # inform code change
                self.tx.put({'pid':os.getpid(), 'status':'changed'})
                self.rx.wait(SPINUP_TIME)
                if self.rx.is_set():
                    return
                self.state = 'RUN'
                self.module_mtimes = {}
            time.sleep(self.poll_interval)

def configure_logging(uri):
    """Configure logging from the PasteDeploy .ini found at uri"""
    config_file = uri
    if config_file.startswith('config:'):
        config_file = config_file.split(':', 1)[1]
    parser = ConfigParser.ConfigParser()
    parser.read([config_file])
    if parser.has_section('loggers'):
        logging.config.fileConfig(config_file)


def serve(server, uri, tx, rx,check_files=None):
    try:
        configure_logging(uri)

        # load wsgi application
        app = paste.deploy.loadapp(uri)

        tx.put({'pid':os.getpid(), 'status':'loaded'})

        server.set_app(app)

        t = threading.Thread(target=server.serve_forever)
        t.setDaemon(True)
        t.start()

        monitor = Monitor(tx=tx, rx=rx,check_files=check_files)
        monitor.periodic_reload()

    except KeyboardInterrupt:
        pass

def reloadwsgi(uri, host='localhost', port=8080, server_name=None, check_files=[],
               stderr="/tmp/reloading_wsgi_server.error"):
    # tx, rx from the subprocess' perspective.

    #tx = Queue(stderr=stderr) # failed to pass in stderr: am setting it at the to of queues.py
    tx = Queue()

    if not server_name:
        server = make_server(host, port, None)
        target = serve
    else:
        server = server_name
        target = serve_from_server

    def spinup():
        rx = Event()
        worker = Process(target=target, args=(server, uri, tx, rx,check_files))
        worker.rx = rx
        worker.start()
        return worker

    spinup()

    while True:
        try:
            msg = tx.get(True, 1)
            sys.stderr.write("%r\n" % msg)
            if msg['status'] == 'changed':
                spinup()
            elif msg['status'] == 'loaded':
                for worker in active_children():
                    if worker.ident != msg['pid']:
                        worker.rx.set()
        except Empty:
            if not active_children():
                return


  
def app_factory(global_config, **local_conf):
    """For testing."""
    import wsgiref.simple_server
    return wsgiref.simple_server.demo_app

if __name__ == "__XXXmain_":
    import reloadwsgi 
    import pkg_resources
    import os.path
    resource = pkg_resources.resource_filename(__name__, 'test_reloadwsgi.ini')
    resource = os.path.abspath(resource)
    print resource,type(resource)
    reloadwsgi.reloadwsgi('config:%s' % resource)


if __name__ == "__main__":
    #aise "main"
    import optparse
    import os.path
    usage = """Usage: %prog [options] config.ini
Robust automatic reloading for WSGI development."""
    parser = optparse.OptionParser(usage)
    parser.add_option("-s", "--s", default=None, dest="server_name",
            help="Load named server from [config.ini] instead of binding to a host and port.")
    parser.add_option("-H", "--host", dest="hostname",
            default="localhost", type="string",
            help="Listen on hostname/address instead of localhost")
    parser.add_option("-p", "--port", dest="port",
            default=8080, type="int",
            help="Listen on hostname/address instead of localhost")
    parser.add_option("-c", "--check_file", dest="check_file",
            default='', type="string",
            help="Restart server when an optional check file changes")
    #parser.add_option("-e", "--log_file", dest="stderr",
    #        default='/tmp/reloading_wsgi_server.error', type="string",
    #        help="Send child process stderr to a file. This is required for reload if the original terminal is closed.")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Must specify exactly one Paste Deploy .ini file.")
    server_name = options.server_name
    check_file = options.check_file
    host = options.hostname
    port = options.port
    config = os.path.abspath(args[0])
    reloadwsgi('config:%s' % config, host=host, port=port,
            server_name=server_name,check_files=[check_file])
