#!/usr/bin/env python

from concurrent.futures import wait
from datetime import datetime
from pathlib import Path

from brewtils import SystemClient
from brewtils.config import load_config
from ruamel.yaml import YAML


def main():
    raw_req = YAML(typ="safe").load(Path("templates/echo.yaml"))

    req = {"_"+k: v for k, v in raw_req.items() if k != "parameters"}
    req.update(raw_req.get("parameters", {}))

    futures = []
    sys_client = SystemClient(**load_config(), blocking=False)

    start = datetime.now()

    for _ in range(250_000):
        futures.append(sys_client.send_bg_request(**req))
    create_end = datetime.now()

    wait(futures)
    wait_end = datetime.now()

    print(f"Started: {start}")
    print(f"Ended: {wait_end}")
    print(f"Creation took: {create_end - start}")
    print(f"Total time: {wait_end - start}")


if __name__ == '__main__':
    main()
