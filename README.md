## Planned use

`docker build -t crczp-ansible-runner .`

`docker run -v /tmp/crczp-tmp/sandboxxx-666/ssh_conf:/root/.ssh -v /tmp/crczp-tmp/sandboxxx-666/inventory.ini:/app/inventory.ini:ro crczp-ansible-runner -u https://github.com/nejake-repo`
