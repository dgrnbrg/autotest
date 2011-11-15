import os, re, time

from autotest_lib.client.bin import utils, test

class asynctest(test.test):
    version = 1

    def run_once(self):
        x = utils.AsyncJob("sleep 1 && echo hi && sleep 1 && echo hi && sleep 1 && echo hi && sleep 1")
        y = utils.AsyncJob("sleep 100")
        time.sleep(2)
        print "job's stdout is now %s" % x.get_stdout()
        res = x.wait_for()
        print "result is %s" % res

        t = time.time()
        y.wait_for(timeout=1)
        print "it took %d to kill the process" % (time.time()-t)
