#/usr/bin/env python
from datetime import datetime
from dotenv import load_dotenv
import os
import sys
import uuid


from fabric.api import env, task, put, sudo, local, cd, lcd, run, prompt
from fabric.colors import red, green, blue, yellow
from fabric.api import shell_env
from fabric.context_managers import cd, prefix, settings, hide



# LANDSCAPES
################################################################################
CREDENTIALS_DIR = "credentials"

# default landscape = localhost (no env.DOCKER_HOST so commands execute locally)

@task
def lada():
    """
    Set fabric env values so docker commands run on the local-Ada server.
    """
    load_dotenv(dotenv_path=os.path.join(CREDENTIALS_DIR, 'lada.env'))
    env.user = os.getenv("PROUCTION_USER")
    env.hosts = os.getenv("PROUCTION_HOST")
    env.DOCKER_HOST = os.getenv("PROUCTION_DOCKER_HOST")

@task
def prod():
    """
    Set fabric env values so docker commands will run on the prod server.
    """
    load_dotenv(dotenv_path=os.path.join(CREDENTIALS_DIR, 'prod.env'))
    env.user = os.getenv("PROUCTION_USER")
    env.hosts = os.getenv("PROUCTION_HOST")
    env.DOCKER_HOST = os.getenv("PROUCTION_DOCKER_HOST")






# DOCKER COMMANDS
################################################################################

@task
def drun(image, options='', command='', args=''):
    cmd = 'docker run '
    cmd += '{} {} {} {}'.format(options, image, command, args)
    dlocal(cmd)

@task
def dstop(container, options=''):
    cmd = 'docker stop '
    cmd += options
    cmd += ' {}'.format(container)
    dlocal(cmd)

@task
def dlogs(container, options=''):
    cmd = 'docker logs '
    cmd += options
    cmd += ' {}'.format(container)
    dlocal(cmd)

@task
def dps(options=''):
    cmd = 'docker ps '
    cmd += options
    dlocal(cmd)

@task
def dshell(container):
    cmd = 'docker exec -ti {} /bin/bash'.format(container)
    dlocal(cmd)

@task
def dexec(container, command, options='-ti'):
    cmd = 'docker exec '
    cmd += options
    cmd += ' {} bash -c \'{}\''.format(container, command)
    dlocal(cmd)

@task
def dsysprune(options=''):
    cmd = 'docker system prune -f '
    cmd += options
    dlocal(cmd)




# FWD DOCKER COMMANDS TO DOCKER HOST
################################################################################

@task
def dlocal(command):
    """
    Execute the `command` (srt) on the remote docker host `env.DOCKER_HOST`.
    If `env.DOCKER_HOST` is not defined, execute `command` on the local docker.
    Docker remote execution via SSH requires remote host to run docker v18+.
    """
    if 'DOCKER_HOST' in env:
        with shell_env(DOCKER_HOST=env.DOCKER_HOST):
            local(command)  # this will run the command on remote docker host
    else:
        local(command)      # this will use local docker (if installed)

