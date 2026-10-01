#!/usr/bin/env python3

import os
import time

import googleapiclient.discovery
from google.oauth2 import service_account

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
ZONE = "us-west1-b"

credentials = service_account.Credentials.from_service_account_file(
    "/srv/service-credentials.json"
)

compute = googleapiclient.discovery.build(
    "compute",
    "v1",
    credentials=credentials
)


def wait_for_operation(operation):
    while True:
        result = compute.zoneOperations().get(
            project=PROJECT,
            zone=ZONE,
            operation=operation["name"]
        ).execute()

        if result["status"] == "DONE":
            if "error" in result:
                raise RuntimeError(result["error"])
            return

        time.sleep(2)


def get_image():
    result = compute.images().getFromFamily(
        project="ubuntu-os-cloud",
        family="ubuntu-2204-lts"
    ).execute()

    return result["selfLink"]


def create_vm2():
    startup_script = """#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip git

cd /home
git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial

cd flask-tutorial
pip3 install ./flaskr
flaskr init-db
nohup flask run -h 0.0.0.0 &
"""

    config = {
        "name": "lab5-vm2",
        "machineType": "zones/us-west1-b/machineTypes/e2-medium",
        "tags": {
            "items": ["allow-5000"]
        },
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": get_image()
                }
            }
        ],
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [
                    {
                        "type": "ONE_TO_ONE_NAT",
                        "name": "External NAT"
                    }
                ]
            }
        ],
        "metadata": {
            "items": [
                {
                    "key": "startup-script",
                    "value": startup_script
                }
            ]
        }
    }

    print("Creating VM-2...")

    operation = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()

    wait_for_operation(operation)

    print("VM-2 created.")


if __name__ == "__main__":
    create_vm2()
