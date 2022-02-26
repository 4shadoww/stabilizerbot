# Import python modules
import datetime
import time
import json
import sys
import threading
import traceback
import logging

from sseclient import SSEClient as EventSource

# Import core modules
from core import config_loader as cfgl
from core import rule_executor
from core import yapi as api
from core import path
from core import timelib

logger = logging.getLogger("infolog")

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

    # TODO Create one function which does all of this with one api call
    if api.stabilized(rev["title"]):
        return False

    if not api.reviewed(rev["title"]):
        return False

    print(api.latest_pending(rev["title"]))
    if not api.latest_pending(rev["title"]):
        return False

    return True

# Object that sends kill signal to ConfigUpdater thread
class Killer:
    kill = False

# Updates config when changed every 30 seconds
class ConfigUpdate(threading.Thread):

    killer = None

    def __init__(self, killer):
        self.killer = killer
        super(ConfigUpdate, self).__init__()

    def run(self):
        if cfgl.cur_conf["core"]["config_mode"] == "online":
            logger.info("online config mode enabled")
        else:
            logger.info("local config mode enabled")

        uf = 30
        times = uf
        while True:
            if self.killer.kill:
                return
            if times >= uf:
                times = 0
                if cfgl.cur_conf["core"]["config_mode"] == "online":
                    cfgl.check_for_online_update()
                else:
                    cfgl.check_for_local_update()

            if self.killer.kill:
                return

            time.sleep(0.5)
            times += 0.5

class Stabilizer(threading.Thread):

    killer = None

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
            api.stabilize(self.rev["title"], reason, expiry=timelib.to_string(dtexpiry))

            return True

        return False

    def run(self):
        times = 0
        while times < cfgl.cur_conf["core"]["s_delay"]:
            if self.killer.kill:
                return False
            time.sleep(0.5)
            times += 0.5

        if should_check(self.rev):
            lock.acquire()
            pending.remove(self.rev["title"])
            lock.release()
            self.stabilize()
        return True

class Worker:
    r_exec = None
    killer = None
    cf_updater = None
    tries = 0

    def __init__(self):
        self.r_exec = rule_executor.Executor()
        # Init ConfigUpdater
        self.killer = Killer()
        self.cf_updater = ConfigUpdate(self.killer)
        self.cf_updater.start()
        tries = 0

    def run(self):
        try:
            wiki = cfgl.cur_conf["core"]["lang"]+"wiki"
            # Event stream
            for event in EventSource(cfgl.cur_conf["core"]["stream_url"]):
                # Filter event stream
                if event.event == 'message':
                    try:
                        change = json.loads(event.data)
                    except ValueError:
                        continue

                    if change["wiki"] == wiki and change["type"] == "edit" and change["namespace"] in cfgl.cur_conf["core"]["namespaces"]:
                        if self.tries != 0:
                            self.tries = 0
                        # Check should revision to be checked at all
                        if should_check(change) and change["title"] not in pending:
                            expiry = self.r_exec.should_stabilize(change)
                            if expiry and not cfgl.cur_conf["core"]["test"] and change["title"] not in pending:
                                lock.acquire()
                                pending.append(change["title"])
                                lock.release()
                                stabilizer = Stabilizer(self.killer, change, expiry)
                                stabilizer.start()

        except KeyboardInterrupt:
            logger.info("terminating stabilizer...")
            self.killer.kill = True
            self.cf_updater.join()
        except ConnectionResetError:
            if self.tries == 5:
                logger.error("giving up")
                self.killer.kill = True
                self.cf_updater.join()
                sys.exit(1)
            logger.error("error: connection error\n trying to reconnect...")
            self.tries += 1
            self.run()
        except:
            logger.error("error: faced unexcepted error check crash report")
            logger.critical(traceback.format_exc())
            logger.info("terminating threads")
            self.killer.kill = True
            self.cf_updater.join()
            sys.exit(1)
