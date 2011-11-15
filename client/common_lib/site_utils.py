from base_utils import *
from threading import Lock, Thread
from StringIO import StringIO
import os, time, signal

class AsyncJob(BgJob):
    def __init__(self, command, stdout_tee=None, stderr_tee=None, verbose=True,
                 stdin=None, stderr_level=DEFAULT_STDERR_LEVEL, kill_func=None):
        super(AsyncJob, self).__init__(command, stdout_tee=stdout_tee,
            stderr_tee=stderr_tee, verbose=verbose, stdin=stdin,
            stderr_level=stderr_level)

        #start time for CmdResult
        self.start_time = time.time()

        if kill_func is None:
            self.kill_func = self._kill_self_process
        else:
            self.kill_func = kill_func

        #we're going to make some threads to drain the stdout and stderr
        def drainer(input, output, lock):
            """
            input is a pipe and output is file-like. if lock is non-None, then
            we assume output isn't threadsafe
            """
            try:
                while True:
                    tmp = os.read(input.fileno(), 1024)
                    if tmp == '':
                        break
                    if lock is not None:
                        lock.acquire()
                    for f in filter(lambda x: x is not None, output):
                        f.write(tmp)
                    if lock is not None:
                        lock.release()
            except:
                pass

        self.stdout_lock = Lock()
        self.stdout_file = StringIO()
        self.stdout_thread = Thread(target=drainer, name=("%s-stdout"%command),
                 args=(self.sp.stdout, (self.stdout_file, self.stdout_tee),
                       self.stdout_lock))
        self.stdout_thread.daemon = True

        self.stderr_lock = Lock()
        self.stderr_file = StringIO()
        self.stderr_thread = Thread(target=drainer, name=("%s-stderr"%command),
                 args=(self.sp.stderr, (self.stderr_file, self.stderr_tee),
                       self.stderr_lock))
        self.stderr_thread.daemon = True

        self.stdout_thread.start()
        self.stderr_thread.start()

    def output_prepare(self, stdout_file=None, stderr_file=None):
        raise NotImplementedError("This object automatically prepares its own "
            "output")

    def process_output(self, stdout=True, final_read=False):
        raise NotImplementedError("This object has background threads "
            "automatically polling the process. Use the locked accessors")

    def get_stdout(self):
        self.stdout_lock.acquire()
        tmp = self.stdout_file.getvalue()
        self.stdout_lock.release()
        return tmp

    def get_stderr(self):
        self.stderr_lock.acquire()
        tmp = self.stderr_file.getvalue()
        self.stderr_lock.release()
        return tmp

    def cleanup(self):
        raise NotImplementedError("This must be waited for to get a result")

    def _kill_self_process(self):
        os.kill(self.sp.pid, signal.SIGTERM)

    def wait_for(self, timeout=None):
        if timeout is None:
            self.sp.wait()

        if timeout > 0:
            start_time = time.time()
            while time.time() - start_time < timeout:
                self.result.exit_status = self.sp.poll()
                if self.result.exit_status is not None:
                    break
        #first need to kill the threads and process, then no more locking
        #issues for superclass's cleanup function
        self.kill_func()

        #we need to fill in parts of the result that aren't done automatically
        self.result.duration = time.time() - self.start_time
        self.result.exit_status = self.sp.poll()
        assert self.result.exit_status is not None

        #make sure we've got stdout and stderr
        self.stdout_thread.join(1)
        self.stderr_thread.join(1)
        assert not self.stdout_thread.is_alive()
        assert not self.stderr_thread.is_alive()

        super(AsyncJob, self).cleanup()

        return self.result
