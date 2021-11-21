#!/usr/bin/env python3
# Copyright 2021 Erik Lönroth
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging
import os
import shutil
from pathlib import Path

from ops.charm import CharmBase
from ops.main import main
from ops.model import MaintenanceStatus, ActiveStatus, WaitingStatus

logger = logging.getLogger(__name__)

class ScpCharm(CharmBase):
    """
    A charm which implements the deployment hooks including the storage hooks.

    foobar_storage_attached -> install -> config_changed -> start

    """

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.data_storage_attached, self._on_data_storage_attached)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.set_ssh_key_action, self._on_set_ssh_key_action)


    def _on_data_storage_attached(self, event):
        """
            [foobar]_storage_attached is a core hook only fireing when
            storage with the name [foobar] defined in metadata.yaml
            The event is a StorageAttachedEvent
        """
        logger.info("STORAGE_ATTACHED")
        self.framework.breakpoint()
        logger.debug(f"Storage id: {self.model.storages['data'][0].id} "
                     f"name: {self.model.storages['data'][0].name} "
                     f"location: {self.model.storages['data'][0].location}")
        self.unit.status = MaintenanceStatus("Preparing install.")

    def _on_install(self, event):
        """
            install is the first core hook to fire when deploying.
        """
        dataLocation = Path(self.model.storages['data'][0].location)
        userHome = dataLocation.parent

        os.system('groupadd scponly')
        os.system(f"useradd -g scponly --home {userHome} --shell /bin/bash scponly")
        os.system(f"mkdir -p {userHome}/.ssh")
        os.system(f"chmod 0700 {userHome}/.ssh")
        os.system(f"chown scponly.scponly {userHome}/.ssh {dataLocation}")

        # Install the restricted-ssh-command package that helps with scp-only-ssh-feature
        os.system("apt install restricted-ssh-commands")
        os.system('mkdir -p /etc/restricted-ssh-commands/')
        shutil.copyfile('templates/etc/restricted-ssh-commands/scponly',
                        '/etc/restricted-ssh-commands/scponly')

        # Install the ubuntu user public keys here?
        # For now, do this in an action.

        self.unit.status = MaintenanceStatus("restricted-ssh-commands installed")

    def _on_config_changed(self, event):
        pass

    def _on_start(self, event):
        """
            Let the user know that a ssh-key is needed to properly set this charm up to serve scp.
        """
        logger.info("Add public ssh key with action: set-ssh-key")
        self.unit.status = WaitingStatus("Waiting on set-ssh-key action.")

    def _on_set_ssh_key_action(self, event):
        userHome = Path(self.model.storages['data'][0].location).parent
        key = event.params['key']
        check_key = True
        if not check_key:
            event.fail("Illegal key entered.")
        else:
            content = f"command=\"/usr/lib/restricted-ssh-commands\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty {key}"
            file = open(f"{userHome}/.ssh/authorized_keys", "w")
            file.write(content)
            file.close()
            os.system(f"chown scponly.scponly {userHome}/.ssh/authorized_keys")
            os.system(f"chmod 0600 {userHome}/.ssh/authorized_keys")
            event.set_results(results={'public-key': key})
            self.unit.status = ActiveStatus("Ready.")


if __name__ == "__main__":
    main(ScpCharm)
