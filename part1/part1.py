#!/usr/bin/env python3

import subprocess
import time

import googleapiclient.discovery
from google.oauth2.credentials import Credentials


PROJECT = "handy-digit-507503-j3"
ZONE = "us-west1-b"
REGION = "us-west1"

INSTANCE_NAME = "lab5-vm"
MACHINE_TYPE = f"zones/{ZONE}/machineTypes/e2-medium"

NETWORK = "global/networks/default"
NETWORK_TAG = "allow-5000"
FIREWALL_RULE = "allow-5000"

IMAGE_PROJECT = "ubuntu-os-cloud"
IMAGE_FAMILY = "ubuntu-2204-lts"


def get_credentials():
    token = subprocess.check_output(
        ["/usr/bin/gcloud", "auth", "print-access-token"]
    ).decode().strip()

    return Credentials(token=token)


credentials = get_credentials()
compute = googleapiclient.discovery.build(
    "compute", "v1", credentials=credentials
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

    image = get_image()

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
                    "sourceImage": image
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
                }
            ]
        }
    }

    print("Creating VM...")

    operation = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()

    wait_for_zonal_operation(operation)

    print("VM created.")


def get_external_ip():
    while True:
        instance = compute.instances().get(
            project=PROJECT,
            zone=ZONE,
            instance=INSTANCE_NAME
        ).execute()

        network_interfaces = instance.get("networkInterfaces", [])

        if network_interfaces:
            access_configs = network_interfaces[0].get(
                "accessConfigs", []
            )

            if access_configs:
                ip = access_configs[0].get("natIP")

                if ip:
                    return ip

        print("Waiting for external IP...")
        time.sleep(2)


def main():
    print("Project:", PROJECT)
    print("Zone:", ZONE)

    create_firewall_rule()
    create_instance()

    ip = get_external_ip()

    print()
    print("Flask application URL:")
    print(f"http://{ip}:5000")


if __name__ == "__main__":
    main()
