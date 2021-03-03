# jupytainer
Scripts for starting a jupter notebook in a container on a remote docker host




## Install
Checkout this repo repo, go into it, then run
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Server setup
In order to run the commands, you need to setup a remote docker host, which is a
linux server (Debian or Ubuntu) in the cloud with the following characteristics:
- Has docker installed and running (you can run `fab install_docker` to do this)
- Has a user allowed to run docker commands (ensure user is in the `docker` group)
- Has ports TCP 8888-8900 open (this is where notebooks will run)

Put the relevant info in `credentials/prod.env` following the example env.


## Usage
To start a new coding environment (Jupyter notebook) for user "juslie" run:

```bash
fab prod jupytainer:"julie"
```

This will start the Jupyter container, run the initialization steps and print the
URL where Julie can access the environment.

The environment and files within it will persist as long as the container is running.


After the event, you can stop and remove the container using
```bash
fab prod dstop:"jupytainer_julie"
fab prod drm:"jupytainer_julie"
```






