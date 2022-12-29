# sftp-server
This charm enables sftp for a sftpuser but restricts ssh login.

The operator uses an action to deploy a public key to be used as the authentication mechanism.

The charm supports using [juju storage] for persistent storage at */srv/sftpuser*

## Usage

Build the charm locally.

    charmcraft build
    juju add-model examples
    juju model-config default-series=focal
    juju model-config logging-config="<root>=WARNING;unit=DEBUG"

Deploy without persitent storage:

    juju deploy ./<charm_name>.charm

... or use persistent storage, from an available juju storage pool:

    $ juju list-storage-pools 
    Name       Provider  Attributes
    loop       loop      
    lxd        lxd       
    lxd-btrfs  lxd       driver=btrfs lxd-pool=juju-btrfs
    lxd-zfs    lxd       driver=zfs lxd-pool=juju-zfs zfs.pool_name=juju-lxd
    rootfs     rootfs    
    tmpfs      tmpfs     

Deploy using the lxd storage pool.

    $ juju deploy ./sftp-server_ubuntu-20.04-amd64.charm --storage data=lxd,200M,1
    
Remote client that wish to copy data to the remote unit creates its ssh key pairs:

    ssh-keygen -f myscp_rsa

The juju operator adds the public key to the unit with a juju action:

    juju run-action sftp-server/0 add-ssh-key key="$(cat ~/myscp_rsa.pub)" --wait

The remote client can now copy data to the data location using the sftpuser user:

    sftp -i ./myscp_rsa sftpuser@192.168.2.144
    put /path/to/file data


## Authors
Erik Lönroth, support me by attributing my work
https://eriklonroth.com

[juju storage]: https://juju.is/docs/olm/defining-and-using-persistent-storage#heading--command-juju-deploy
