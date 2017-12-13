import sys
import random
import time
import logging
import inspect
from contextlib import contextmanager

class ProgressPrinter(object):
    def __init__(self, size=100):
        self.processes = {}
        self.progress = ""
        self.id_array = range(100,100+size)
        self.used_id_array = []

    def newProcess(self, name, total, level=0):
        id = self.generateNewId()
        pproc = ProgressProcess(self, name, total, id, level)
        self.processes.update({id: pproc})
        return pproc

    @contextmanager
    def monitoredProcess(self, total=1, level=0):
        caller = inspect.stack()[2][3]
        id = self.generateNewId()
        pproc = ProgressProcess(self, caller, total, id, level)
        self.processes.update({id: pproc})
        yield pproc.start()
        pproc.finish()

    def generateNewId(self):
        start = random.randrange(0, len(self.id_array))
        for i in range(len(self.id_array)):
            i = (i+start)%len(self.id_array)
            if i not in self.used_id_array:
                self.used_id_array.append(i)
                return self.id_array[i]
        raise Exception("Too many processes. Consider defining a higher size when initializing the ProgressPrinter object.")

    def printProgressP(self, text):
        sys.stdout.write("\r{}".format(text))
        sys.stdout.flush()

    def printProgressV(self, text):
        sys.stdout.write("{}\n".format(text))

class ProgressProcess(object):
    def __init__(self, pp, name, total, id, level):
        self.pp = pp
        self.name = name
        self.total = total
        self.level = self.indentLevel(level)
        self.type = None
        self.value = 0

    def indentLevel(self, level):
        l = ""
        for i in range(level):
            l += "  "
        return l

    def start(self):
        s = "{0}Starting Process: {1}".format(self.level, self.name)
        sys.stdout.write("[{}] {}\n".format(time.strftime('%a %H:%M:%S'),s))
        logging.info(s)
        return self

    def updateProgressP(self):
        if self.type != "V":
            self.type = "P"
            self.value += 1
            self.pp.printProgressP("[{0}] {1}>>Progress: {2}%".format(time.strftime('%a %H:%M:%S'),
                self.level, round(self.value/float(self.total)*100,1)))

    def updateProgressV(self):
        if self.type != "P":
            self.type = "V"
            self.value += 1
            self.pp.printProgressV("[{0}] {1}>>Progress: ({2}/{3})".format(time.strftime('%a %H:%M:%S'),
                self.level, self.value, self.total))

    def finish(self):
        s = "{0}Finished Process: {1}".format(self.level, self.name)
        sys.stdout.write("{0}[{1}] {2}\n".format("\n" if self.type=="P" else "",time.strftime('%a %H:%M:%S'),s))
        logging.info(s)
