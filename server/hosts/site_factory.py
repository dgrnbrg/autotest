from autotest_lib.client.common_lib import utils, global_config
import logging, subprocess, os

class AsyncSSHMixin(object):
    def __init__(self, *args, **kwargs):
        super(AsyncSSHMixin, self).__init__(*args, **kwargs)

    def run_async(self, command, stdout_tee=None, stderr_tee=None, args=(),
                  connect_timeout=30, options='', verbose=True,
                  stderr_level=utils.DEFAULT_STDERR_LEVEL,
                  cmd_outside_subshell=''):
        """
        Run a command on the remote host. Returns an AsyncJob object to
        interact with the remote process.

        Sorry, but you can't use stdin--that's how we do job control.

        This is mostly copied from SSHHost.run and SSHHost._run
        """
        if verbose:
            logging.debug("Running (async ssh) '%s'" % command)

        # Start a master SSH connection if necessary.
        self.start_master_ssh()

        env = " ".join("=".join(pair) for pair in self.env.iteritems())

        ssh_cmd = self.ssh_command(connect_timeout, options)
        if not env.strip():
            env = ""
        else:
            env = "export %s;" % env
        for arg in args:
            command += ' "%s"' % utils.sh_escape(arg)
        full_cmd = '{ssh_cmd} "{env} {cmd} {killer_bits}"'.format(
            ssh_cmd = ssh_cmd, env = env,
            cmd = utils.sh_escape("%s (%s)" % (cmd_outside_subshell, command)),
            killer_bits = utils.sh_escape("& read; kill -9 $!"))

        job = utils.AsyncJob(full_cmd, stdout_tee=stdout_tee,
                              stderr_tee=stderr_tee, verbose=verbose,
                              stderr_level=stderr_level,
                              stdin=subprocess.PIPE)

        def kill_func():
            #this triggers the remote kill
            os.write(job.sp.stdin.fileno(), "lulz\n")
            utils.nuke_subprocess(job.sp)

        job.kill_func = kill_func

        return job

SSH_ENGINE = global_config.global_config.get_config_value('AUTOSERV',
                                                          'ssh_engine',
                                                          type=str)

def postprocess_classes(classes, hostname, **args):
    if SSH_ENGINE != 'raw_ssh':
        raise RuntimeError('Must use raw_ssh for async support!')

    classes.append(AsyncSSHMixin)
