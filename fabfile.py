#/usr/bin/env python
from datetime import datetime
from dotenv import load_dotenv
import json
import os
import sys
import time
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



# JUPYTER NOTEBOOK
################################################################################

def find_used_ports():
    with hide('stdout', 'running'):
        ps_data_jsonl = dlocal("docker ps --format='{{json .}}'", capture=True)
    used_ports = set()
    for line in ps_data_jsonl.stdout.split('\n'):
        ps_data = json.loads(line)
        ports_info = ps_data["Ports"]
        if ports_info.count('>') != 1:
            continue
        port = ports_info.split('>')[1].split('/')[0]
        used_ports.add(int(port))
    return used_ports

def find_unused_port():
    all_ports = set(n for n in range(8888, 8988+1))
    unused_ports = all_ports - find_used_ports()
    unused_port = sorted(unused_ports)[0]
    print(unused_port)
    return unused_port

@task
def jupytainer(username, token=None):
    port = str(find_unused_port())
    options =  f"  -p {port}:{port}"
    container_name = f"jupytainer_{username}"
    options += f" --name {container_name}"
    image = "jupyter/minimal-notebook:latest"
    command = "start-notebook.sh"
    token = token if token else "mp84"
    args =  f" --NotebookApp.token='{token}'"
    args +=  f" --port={port}"
    args += " --no-browser &"
    drun(image, options=options, command=command, args=args)
    time.sleep(3)
    dexec(container_name, command="git clone https://github.com/ygingras/mp-84-atelier", options="")
    print(green("Notebook env ready..."))
    print(blue(f"Visit  http://{env.hosts}:{port}/?token={token}"))



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
def drm(container, options=''):
    cmd = 'docker rm '
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
def dlocal(command, capture=False):
    """
    Execute the `command` (srt) on the remote docker host `env.DOCKER_HOST`.
    If `env.DOCKER_HOST` is not defined, execute `command` on the local docker.
    Docker remote execution via SSH requires remote host to run docker v18+.
    """
    if 'DOCKER_HOST' in env:
        with shell_env(DOCKER_HOST=env.DOCKER_HOST):
            return local(command, capture=capture)  # run on remote docker host
    else:
        return local(command, capture=capture)      # run on localhost docker



# PROVISION DOCKER ON REMOTE HOST
################################################################################

@task
def install_docker():
    """
    Install docker on remote host following the instructions from the docs:
    https://docs.docker.com/engine/install/debian/#install-using-the-repository
    """
    with settings(warn_only=True), hide('stdout', 'stderr', 'warnings'):
        sudo('apt-get -qy remove docker docker-engine docker.io containerd runc')
    with hide('stdout'):
        sudo('apt-get update -qq')
        sudo('apt-get -qy install apt-transport-https ca-certificates curl gnupg-agent software-properties-common')
    sudo('curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -')
    sudo('add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"')
    with hide('stdout'):
        sudo('apt-get update -qq')
        sudo('apt-get -qy install docker-ce docker-ce-cli containerd.io')
    sudo('usermod -aG docker {}'.format(env.user))  # add user to `docker` group
    sudo("sed -i 's/^#MaxSessions 10/MaxSessions 30/' /etc/ssh/sshd_config")
    # docker-compose opens >10 SSH sessions, hence the need to up default value
    # via https://github.com/docker/compose/issues/6463#issuecomment-458607840
    # TODO sysctl -w vm.max_map_count=262144
    sudo('service sshd restart')
    print(green('Docker installed on ' + env.host))


@task
def uninstall_docker(deep=False):
    """
    Uninstall docker using instructions from the official Docker docs:
    https://docs.docker.com/engine/install/debian/#uninstall-docker-engine
    """
    deep = (deep and deep.lower() == 'true')  # defaults to False
    with hide('stdout'):
        sudo('apt-get -qy purge docker-ce docker-ce-cli containerd.io')
        if deep:
            sudo('rm -rf /var/lib/docker')
            sudo('rm -rf /var/lib/containerd')
    print(green('Docker uninstalled from ' + env.host))

