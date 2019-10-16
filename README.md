## Planned use

`docker build -t csirtmu/kypo-ansible-runner .` 

`docker run -v /tmp/kypo-tmp/sandboxxx-666/ssh_conf:/root/.ssh -v /tmp/kypo-tmp/sandboxxx-666/inventory.ini:/app/inventory.ini:ro csirtmu/kypo-ansible-runner -r https://github.com/KYPO/nejake-repo`