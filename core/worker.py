# Import python modules
import datetime
import time
import json
import sys
import threading
import traceback
import logging
import os

from requests_sse import EventSource, InvalidStatusCodeError, InvalidContentTypeError
import requests

# Import core modules
from core import config_loader as cfgl
from core import rule_executor
from core import yapi as api
from core import timelib

LOG = logging.getLogger("infolog")

lock = threading.Lock()
pending = []

def should_check(rev):
    delta = datetime.timedelta(hours=1)

    # Check should revision to be checked at all
    revs = api.get_revision([rev["revision"]["new"]])

    if "badrevids" in revs["query"]:
        return False

    # Skip change if it's too old. Eventstream does seem to stream sometimes even months old revisions for some reason?
    if datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(rev["timestamp"]) > delta:
        return False

    # Merged logic api.stabilized, api.reviewed and api.latest_pending
    # Checks is page stabilised already, is page reviewed and is lastest change pending
    if not api.should_check(rev["title"]):
        return False

    return True

# Object that sends kill signal to ConfigUpdater thread
class Killer:
    kill = False

# Updates config when changed every 30 seconds
class ConfigUpdate(threading.Thread):

    killer: Killer

    def __init__(self, killer):
        self.killer = killer
        super(ConfigUpdate, self).__init__()

    def run(self):
        if cfgl.cur_conf["core"]["config_mode"] == "online":
            LOG.info("online config mode enabled")
        else:
            LOG.info("local config mode enabled")

        uf = 30
        times = uf
        while True:
            if self.killer.kill:
                LOG.info('ConfigUpdate: thread terminated')
                return
            if times >= uf:
                times = 0
                if cfgl.cur_conf["core"]["config_mode"] == "online":
                    cfgl.check_for_online_update()
                else:
                    cfgl.check_for_local_update()

            if self.killer.kill:
                LOG.info('ConfigUpdate: thread terminated')
                return

            time.sleep(0.5)
            times += 0.5

class Stabilizer(threading.Thread):

    killer: Killer

    def __init__(self, killer, rev, expiry):
        self.killer = killer
        self.rev = rev
        self.expiry = expiry
        super(Stabilizer, self).__init__()


    def stabilize(self):
        if not cfgl.cur_conf["core"]["reverted"] and api.is_reverted(self.rev["title"], self.rev["revision"]["new"]):
            return False

        if not cfgl.cur_conf["core"]["test"] and not cfgl.cur_conf["core"]["test"]:
            # Calculate expiry
            dtexpiry = datetime.datetime.utcnow() + datetime.timedelta(hours=self.expiry, minutes=0, seconds=0)
            # Set reason
            revlink = "[[Special:Diff/"+str(self.rev["revision"]["new"])+"|"+str(self.rev["revision"]["new"])+"]]"
            reason = cfgl.dictionary[cfgl.cur_conf["core"]["lang"]]["reasons"]["YV1"] % revlink

            # Stabilize
            return api.stabilize(self.rev["title"], reason, expiry=timelib.to_string(dtexpiry))


        return False

    def run(self):
        times = 0
        while times < cfgl.cur_conf["core"]["s_delay"]:
            if self.killer.kill:
                return

            time.sleep(0.5)
            times += 0.5

        if should_check(self.rev):
            lock.acquire()
            pending.remove(self.rev["title"])
            lock.release()
            if not self.stabilize():
                # Hack to exit the program when stabilize fails
                # And that's because the session is probably gone bad
                # So just exit with error and restart whole shit
                os._exit(1)


class Worker:
    r_exec: rule_executor.Executor
    killer: Killer
    cf_updater: ConfigUpdate
    tries = 0

    def __init__(self):
        self.r_exec = rule_executor.Executor()
        # Init ConfigUpdater
        self.killer = Killer()
        self.cf_updater = ConfigUpdate(self.killer)
        self.cf_updater.start()
        self.tries = 0


    def run(self):
        try:
            wiki = cfgl.cur_conf['core']['lang'] + 'wiki'

            with EventSource(cfgl.cur_conf['core']['stream_url'], timeout=30) as event_source:
                # Event stream
                for event in event_source:
                    # Filter event stream
                    if event.type != 'message':
                        continue
                    try:
                        change = json.loads(event.data)
                    except ValueError:
                        continue

                    if 'wiki' not in change or \
                       'type' not in change or \
                       'namespace' not in change or \
                       change['wiki'] != wiki or \
                       change['type'] != 'edit' or \
                       change['namespace'] not in cfgl.cur_conf['core']['namespaces']:
                        continue

                    if self.tries != 0:
                        self.tries = 0

                    # Check should revision to be checked at all
                    if change['title'] in pending or not should_check(change):
                        continue

                    expiry = self.r_exec.should_stabilize(change)

                    # Last checks
                    lock.acquire()
                    if cfgl.cur_conf['core']['test'] or not expiry or change['title'] in pending:
                        continue

                    # Stabilize
                    pending.append(change['title'])
                    lock.release()
                    stabilizer = Stabilizer(self.killer, change, expiry)
                    stabilizer.start()

        except KeyboardInterrupt:
            LOG.info("terminating stabilizer...")
            self.killer.kill = True
            self.cf_updater.join()
            sys.exit(0)

        except requests.RequestException:
            if self.tries == 5:
                LOG.error("giving up")
                self.killer.kill = True
                self.cf_updater.join()
                sys.exit(1)
            LOG.error("error: connection error\n trying to reconnect...")
            self.tries += 1
            self.run()

        except:
            LOG.error("error: faced unexcepted error check crash report")
            LOG.critical(traceback.format_exc())
            LOG.info("terminating threads")
            self.killer.kill = True
            self.cf_updater.join()
            LOG.info("threads terminated")

        sys.exit(1)
