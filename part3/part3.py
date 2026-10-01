#!/usr/bin/env python3

import os
import time

import googleapiclient.discovery
from google.oauth2 import service_account


PROJECT = "handy-digit-507503-j3"
ZONE = "us-west1-b"
REGION = "us-west1"

INSTANCE_NAME = "lab5-vm1"
MACHINE_TYPE = f"zones/{ZONE}/machineTypes/e2-medium"

NETWORK = "global/networks/default"
NETWORK_TAG = "allow-5000"
FIREWALL_RULE = "allow-5000"

IMAGE_PROJECT = "ubuntu-os-cloud"
IMAGE_FAMILY = "ubuntu-2204-lts"


credentials = service_account.Credentials.from_service_account_file(
    filename="service-credentials.json"
)

compute = googleapiclient.discovery.build(
    "compute",
    "v1",
    credentials=credentials
)


def wait_for_operation(operation):
    while True:
        result = compute.globalOperations().get(
            project=PROJECT,
            operation=operation["name"]
        ).execute()

        if result["status"] == "DONE":
            if "error" in result:
                raise RuntimeError(result["error"])
            return

        time.sleep(2)


def wait_for_zonal_operation(operation):
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
        project=IMAGE_PROJECT,
        family=IMAGE_FAMILY
    ).execute()

    return result["selfLink"]


def create_firewall_rule():
    try:
        compute.firewalls().get(
            project=PROJECT,
            firewall=FIREWALL_RULE
        ).execute()

        print("Firewall rule already exists.")

    except Exception:
        print("Creating firewall rule...")

        firewall_body = {
            "name": FIREWALL_RULE,
            "network": NETWORK,
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": [NETWORK_TAG],
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": ["5000"]
                }
            ]
        }

        operation = compute.firewalls().insert(
            project=PROJECT,
            body=firewall_body
        ).execute()

        wait_for_operation(operation)

        print("Firewall rule created.")


def create_instance():
    with open("vm1-startup-script.sh", "r") as f:
        startup_script = f.read()

    with open("vm1-launch-vm2-code.py", "r") as f:
        vm1_launch_code = f.read()

    with open("vm2-startup-script.sh", "r") as f:
        vm2_startup_script = f.read()

    with open("service-credentials.json", "r") as f:
        service_credentials = f.read()

    config = {
        "name": INSTANCE_NAME,
        "machineType": MACHINE_TYPE,

        "tags": {
            "items": [NETWORK_TAG]
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
                "network": NETWORK,
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
                },
                {
                    "key": "vm2-startup-script",
                    "value": vm2_startup_script
                },
                {
                    "key": "service-credentials",
                    "value": service_credentials
                },
                {
                    "key": "vm1-launch-vm2-code",
                    "value": vm1_launch_code
                },
                {
                    "key": "project",
                    "value": PROJECT
                }
            ]
        }
    }

    print("Creating VM-1...")

    operation = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()

    wait_for_zonal_operation(operation)

    print("VM-1 created.")


def main():
    print("Project:", PROJECT)
    print("Zone:", ZONE)

    create_firewall_rule()
    create_instance()


if __name__ == "__main__":
    main()
