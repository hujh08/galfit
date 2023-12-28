#!/usr/bin/env python3

'''
    utilities used for galfit
'''

import subprocess

# run system command
def run_system_cmd(cmd, stdout=True, timeout=None, **kwargs):
    '''
        run system command

        return: exit code
    '''
    # stdout
    if isinstance(stdout, bool):
        if not stdout:
            kwargs['stdout']=subprocess.DEVNULL
    else:
        kwargs['stdout']=stdout

    # timeout
    if timeout is not None:
        kwargs['timeout']=timeout

    stat=subprocess.run(cmd, **kwargs)
    return stat.returncode
