#!/usr/bin/env python

from pathlib import Path

from brewtils import SystemClient
from brewtils.config import load_config
from ruamel.yaml import YAML


def main():
    raw_req = YAML(typ="safe").load(Path("templates/echo.yaml"))

    req = {"_"+k: v for k, v in raw_req.items() if k != "parameters"}
    req.update(raw_req.get("parameters", {}))

    sys_client = SystemClient(**load_config())
    sys_client.send_bg_request(**req)


if __name__ == '__main__':
    main()
