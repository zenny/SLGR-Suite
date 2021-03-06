from datetime import datetime
import pickle
import subprocess
import logging.handlers
import logging
import sys
import time
import os


class FlagIO(object):
    """Base object for logging and shared memory flag read/write operations"""

    def __init__(self, subprogram=False, delay=0.1):
        self.subprogram = subprogram
        self.delay = delay

        logging.captureWarnings(True)
        self.logger = logging.getLogger(type(self).__name__)
        formatter = logging.Formatter(
            '{asctime} | {levelname:7} | {name:<11} | {funcName:<20} |'
            ' {message}', style='{')
        self.logfile = logging.handlers.RotatingFileHandler(Flags().log,
                                                            backupCount=20)
        self.tf_logfile = logging.handlers.RotatingFileHandler(
            os.path.splitext(Flags().log)[0] + ".tf" +
            os.path.splitext(Flags().log)[1], backupCount=20)

        self.logfile.setFormatter(formatter)
        self.tf_logfile.setFormatter(formatter)
        # don't re-add the same handler
        if not str(self.logfile) in str(self.logger.handlers):
            self.logger.addHandler(self.logfile)

        self.flagpath = self.init_ramdisk()

        try:
            if self.read_flags().cli:
                self.logstream = logging.StreamHandler()
                self.logstream.setFormatter(formatter)
                if not str(self.logstream) in str(self.logger.handlers):
                    self.logger.addHandler(self.logstream)
        except AttributeError:
            pass

        if subprogram:
            self.read_flags()
            try:
                if self.flags.verbalise:
                    self.logger.setLevel(logging.DEBUG)
                else:
                    self.logger.setLevel(logging.INFO)
            except AttributeError:
                self.logger.setLevel(logging.DEBUG)
            try:
                f = open(self.flagpath)
                f.close()
            except FileNotFoundError:
                time.sleep(1)

    def send_flags(self):
        self.logger.debug(self.flags)
        with open(r"{}".format(self.flagpath), "wb") as outfile:
            pickle.dump(self.flags, outfile)

    def read_flags(self):
        inpfile = None
        count = 0
        while inpfile is None:  # retry-while inpfile is None and count < 10:
            count += 1
            try:
                with open(r"{}".format(self.flagpath), "rb") as inpfile:
                    try:
                        time.sleep(self.delay)
                        flags = pickle.load(inpfile)
                    except EOFError:
                        self.logger.warning("Flags Busy: Reusing old")
                        flags = self.flags
                    self.flags = flags
                    self.logger.debug(self.flags)
                    return self.flags
            except FileNotFoundError:
                if count > 10:
                    break
                else:
                    time.sleep(self.delay)

    def io_flags(self):
        self.send_flags()
        self.flags = self.read_flags()

    def init_ramdisk(self):
        flagfile = ".flags.pkl"
        if sys.platform == "darwin":
            ramdisk = "/Volumes/RAMDisk"
            if not self.subprogram:
                proc = subprocess.Popen(['./libs/scripts/RAMDisk', 'mount'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
                stdout, stderr = proc.communicate()
                for line in stdout.decode('utf-8').splitlines():
                    self.logger.info(line)
                if stderr:
                    self.logger.debug(stderr.decode('utf-8'))
                time.sleep(self.delay)  # Give the OS time to finish
        else:
            ramdisk = "/dev/shm"
        flagpath = os.path.join(ramdisk, flagfile)
        return flagpath

    def cleanup_ramdisk(self):
        if sys.platform == "darwin":
            proc = subprocess.Popen(['./libs/scripts/RAMDisk', 'unmount'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            stdout, stderr = proc.communicate()
            for line in stdout.decode('utf-8').splitlines():
                self.logger.info(line)
            if stderr:
                self.logger.debug(stderr.decode('utf-8'))
        else:
            os.remove(self.flagpath)


class Flags(dict):
    """
    Allows you to set and get {key: value} pairs like attributes.
    This allows compatibility with argparse.Namespace objects.
    """

    def __init__(self, defaults=True):
        if defaults:
            # All paths are relative to slgrSuite.py
            self.annotation = './data/committedframes/'
            self.backup = './data/ckpt/'
            self.batch = 16
            self.binary = './data/bin/'
            self.built_graph = './data/built_graph/'
            self.capdevs = []
            self.cli = False
            self.clip = False
            self.clip_norm = 5
            self.clr_mode = "triangular2"
            self.config = './data/cfg/'
            self.dataset = './data/committedframes/'
            self.demo = ''
            self.done = False
            self.epoch = 1
            self.error = ""
            self.fbf = ''
            self.gpu = 0.0
            self.gpu_name = '/gpu:0'
            self.grayscale = False
            self.imgdir = './data/sample_img/'
            self.img_out = './data/img_out/'
            self.output_type = []
            self.keep = 20
            self.kill = False
            self.labels = './data/predefined_classes.txt'
            self.load = -1
            self.log = './data/logs/flow.log'
            self.lr = 1.0e-5
            self.max_lr = 1.0e-5
            self.model = ''
            self.momentum = 0.0
            self.progress = 0.0
            self.project_name = "default"
            self.save = 16000
            self.freeze = False
            self.save_video = True
            self.size = 0
            self.started = False
            self.step_size_coefficient = 2
            self.summary = './data/summaries/'
            self.threshold = 0.4
            self.timeout = 0
            self.trainer = 'rmsprop'
            self.verbalise = False
            self.video_out = "./data/video_out/"
            self.train = False
            self.pb_load = False
            self.meta_load = False

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __getstate__(self):
        pass

    def get_defaults(self):
        self.__init__()
