#!/usr/bin/env python3

import subprocess
import time

import googleapiclient.discovery
from google.oauth2.credentials import Credentials


PROJECT = "handy-digit-507503-j3"
ZONE = "us-west1-b"

SNAPSHOT_NAME = "base-snapshot-lab5-vm"
MACHINE_TYPE = f"zones/{ZONE}/machineTypes/e2-medium"
NETWORK = "global/networks/default"

INSTANCE_NAMES = [
    "lab5-clone-1",
    "lab5-clone-2",
    "lab5-clone-3",
]


def get_credentials():
    token = subprocess.check_output(
        ["/usr/bin/gcloud", "auth", "print-access-token"]
    ).decode().strip()

    return Credentials(token=token)


credentials = get_credentials()

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

        time.sleep(1)


def create_instance(instance_name):
    start_time = time.time()

    snapshot_url = (
        f"projects/{PROJECT}/global/snapshots/{SNAPSHOT_NAME}"
    )

    config = {
        "name": instance_name,
        "machineType": MACHINE_TYPE,
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceSnapshot": snapshot_url
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
        ]
    }

    print(f"Creating {instance_name}...")

    operation = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()

    wait_for_operation(operation)

    elapsed = time.time() - start_time

    print(f"{instance_name} created in {elapsed:.2f} seconds")

    return elapsed


def main():
    print(f"Using snapshot: {SNAPSHOT_NAME}")
    print(f"Zone: {ZONE}")
    print()

    timings = []

    for instance_name in INSTANCE_NAMES:
        elapsed = create_instance(instance_name)
        timings.append((instance_name, elapsed))

    print()
    print("Creation times:")

    for instance_name, elapsed in timings:
        print(f"{instance_name}: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
