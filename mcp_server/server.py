# server.py
import json
import logging
import os
from dataclasses import field, make_dataclass
from pathlib import Path

import uvicorn
from brewtils import EasyClient, SystemClient
from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform
from fastmcp.utilities.logging import get_logger

logging.basicConfig(level=logging.INFO)
logger = get_logger("bg_fastmpc")

# Initialize FastMCP
mcp = FastMCP(name="MCP_Beergarden")

bg_connection_args = {
    "bg_host": os.environ.get("MCP_BG_HOST", "localhost"),
    "bg_port": int(os.environ.get("MCP_BG_PORT", 2337)),
    "ssl_enabled": os.environ.get("MCP_BG_SSL", "false").lower() == "true",
}

bg_url_prefix = os.environ.get("MCP_BG_URL_PREFIX", None)
if bg_url_prefix and bg_url_prefix != "":
    bg_connection_args["bg_url_prefix"] = bg_url_prefix

ca_cert = os.environ.get("MCP_BG_CA_CERT", None)
if ca_cert and ca_cert != "":
    bg_connection_args["ca_cert"] = ca_cert

client_cert = os.environ.get("MCP_BG_CLIENT_CERT", None)
if client_cert and client_cert != "":
    bg_connection_args["client_cert"] = client_cert

client_key = os.environ.get("MCP_BG_CLIENT_KEY", None)
if client_key and client_key != "":
    bg_connection_args["client_key"] = client_key


tags = []
for bg_tag in os.environ.get("MCP_BG_TAGS", "").split(","):
    if bg_tag != "":
        tags.append(bg_tag)

bg_whitelist = os.environ.get("MCP_BG_WHITELIST", "whitelist.json")

whitelist_options = None
valid_whitelist_keys = [
    "namespace",
    "system_name",
    "system_version",
    "instance_name",
    "command",
]

if bg_whitelist:
    whitelist_path = Path(bg_whitelist)

    if whitelist_path.is_file():
        with open(whitelist_path, "r") as file:
            whitelist_json = json.load(file)
            if "whitelist" in whitelist_json and isinstance(
                whitelist_json["whitelist"], list
            ):
                whitelist_options = whitelist_json["whitelist"]
    else:
        logger.error(f"Failed to load white list commands at {bg_whitelist}")


def run_cmd(
    namespace: str,
    system_name: str,
    instance_name: str,
    system_version: str,
    command_name: str,
    parameters: dict,
):
    logger.info(
        f"Ran {namespace}-{system_name}-{instance_name}-{system_version}-{command_name}"
    )
    request = getattr(
        SystemClient(
            system_name=system_name,
            system_namespace=namespace,
            default_instance=instance_name,
            **bg_connection_args,
        ),
        command_name,
    )(_blocking=True, **parameters)

    if request.error:
        return request.error_message

    return request.output


def parameter_type_mapping(parameter_type: str):

    if parameter_type == "String":
        return str
    if parameter_type == "Integer":
        return int
    if parameter_type == "Float":
        return float
    if parameter_type == "Boolean":
        return bool
    if parameter_type == "Date":
        return int
    if parameter_type == "DateTime":
        return int
    return dict


def generate_commands():
    client = EasyClient(**bg_connection_args)
    systems = client.find_systems()

    for system in systems:
        for instance in system.instances:
            for command in system.commands:

                if (whitelist_options and len(whitelist_options) > 0) or (
                    tags and len(tags) > 0
                ):
                    include = False

                    # Check Tags
                    if (
                        tags
                        and len(tags) > 0
                        and command.tags
                        and len(command.tags) > 0
                    ):
                        for tag in command.tags:
                            if tag in tags:
                                include = True

                    if not include and whitelist_options and len(whitelist_options) > 0:
                        for option in whitelist_options:

                            # Verify at least one required field is set
                            if any(key in option for key in valid_whitelist_keys):
                                if (
                                    "namespace" not in option
                                    or len(option["namespace"]) == 0
                                    or option["namespace"] == system.namespace
                                ):
                                    if (
                                        "system_name" not in option
                                        or len(option["system_name"]) == 0
                                        or option["system_name"] == system.name
                                    ):
                                        if (
                                            "system_version" not in option
                                            or len(option["system_version"]) == 0
                                            or option["system_version"]
                                            == system.version
                                        ):
                                            if (
                                                "instance_name" not in option
                                                or len(option["instance_name"]) == 0
                                                or option["instance_name"]
                                                == instance.name
                                            ):
                                                if (
                                                    "command" not in option
                                                    or len(option["command"]) == 0
                                                    or option["command"] == command.name
                                                ):
                                                    include = True

                else:
                    include = True

                if include:
                    inputs = []
                    for parameter in command.parameters:
                        if parameter.default:
                            # Must setup default_factory for list and dict types
                            if isinstance(parameter.default, (list, dict)):
                                parameter.default = field(
                                    default_factory=parameter.default
                                )
                            inputs.append(
                                (
                                    parameter.key,
                                    parameter_type_mapping(parameter.type),
                                    parameter.default,
                                )
                            )
                        else:
                            inputs.append(
                                (parameter.key, parameter_type_mapping(parameter.type))
                            )

                    # Sort inputs by tuple length to push parameters with defaults to end of list
                    inputs.sort(key=len)

                    logger.info(
                        f"Loading {system.namespace}-{system.name}-{instance.name}-{system.version}-{command.name}"
                    )
                    mcp.add_tool(
                        Tool.from_tool(
                            tool=run_cmd,
                            name=f"{system.namespace}-{system.name}-{system.version}-{instance.name}_{command.name}",
                            title=(
                                command.display_name
                                if command.display_name
                                else command.name
                            ),
                            description=f"Namespace={system.namespace} System={system.name} Version={system.version} Instance={instance.name} Description={command.description}",
                            meta={
                                "namespace": system.namespace,
                                "system": system.name,
                                "version": system.version,
                                "instance": instance.name,
                            },
                            transform_args={
                                # Set from looped system
                                "namespace": ArgTransform(
                                    hide=True, default=system.namespace
                                ),
                                "system_name": ArgTransform(
                                    hide=True, default=system.name
                                ),
                                "system_version": ArgTransform(
                                    hide=True, default=system.version
                                ),
                                "instance_name": ArgTransform(
                                    hide=True, default=instance.name
                                ),
                                "command_name": ArgTransform(
                                    hide=True, default=command.name
                                ),
                                # Override a default schema
                                "parameters": ArgTransform(
                                    type=make_dataclass("Parameters", inputs)
                                ),
                            },
                        )
                    )


generate_commands()

# Create the ASGI application app for production servers
app = mcp.http_app(stateless_http=True)

if __name__ == "__main__":
    # Fallback for local python execution: transport="http" invokes Streamable HTTP
    # IMPORTANT: Must bind to 0.0.0.0 inside Docker
    uvicorn.run(
        "server:app",
        host=os.environ.get("MCP_BIND_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_BIND_port", 8000)),
        log_level="info",
    )
