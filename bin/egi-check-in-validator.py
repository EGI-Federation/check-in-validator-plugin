#!/usr/bin/env python3

import argparse
import configparser
import json
import logging
import logging.config
import os
import select
import sys

TIMEOUT = 5
PLUGIN_CONFIG_PATHS = [
    "/etc/egi-check-in-validator/egi-check-in-validator.ini",
]
# Setup logger
log = logging.getLogger(__name__)
LOGGER_CONFIG_PATH = "/etc/egi-check-in-validator/logger.ini"


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="path of the configuration file.")
    args = parser.parse_args()
    return vars(args)


def read_config_file(arguments):
    global PLUGIN_CONFIG_PATHS
    global LOGGER_CONFIG_PATH
    filename = None
    error_message_header = "[egi-check-in-validator] Parsing configuration: "
    paths = [arguments["config"]] + PLUGIN_CONFIG_PATHS
    for path in paths:
        if path and os.path.exists(path):
            filename = path
    if not filename:
        log.error(error_message_header + "Configuration file was not found.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(filename)
    if "logger" in config:
        logger_path = config["logger"]["config_path"]
    else:
        logger_path = LOGGER_CONFIG_PATH
    logging.config.fileConfig(logger_path, disable_existing_loggers=False)
    mappings = {}
    for key, value in config.items("mappings"):
        value = value.rstrip()
        line = value.split(" ")
        if len(line) == 5:
            error_message = '"{}" Mapper: {} cannot be "*". Please enter a valid value.'
            if line[1] == "*":
                log.error(error_message_header + error_message.format(key, "ISSUER"))
                sys.exit(1)
            if line[4] == "*":
                log.error(error_message_header + error_message.format(key, "GROUP"))
                sys.exit(1)
        else:
            log.error(error_message_header + '"{}" Mapper: invalid mapping configuration'.format(key))
            sys.exit(1)
        mappings[key] = {
            "unique_id": line[0],
            "issuer": line[1],
            "audience": line[2],
            "scope": line[3],
            "group": line[4],
        }
    return mappings, filename


# Get environment variables
def parse_env_variables():
    unique_id = os.getenv("BEARER_TOKEN_0_CLAIM_voperson_id_0")
    if unique_id is None:
        unique_id = os.getenv("BEARER_TOKEN_0_CLAIM_sub_0")
    issuer = os.getenv("BEARER_TOKEN_0_CLAIM_iss_0")
    audience = os.getenv("BEARER_TOKEN_0_CLAIM_aud_0")
    idx = 0
    eduperson_entitlement = []
    while True:
        group = os.getenv("BEARER_TOKEN_0_CLAIM_eduperson_entitlement_" + str(idx))
        if group is None:
            break
        eduperson_entitlement.append(group)
        idx += 1
    idx = 0
    scopes = []
    while True:
        group = os.getenv("BEARER_TOKEN_0_SCOPE_" + str(idx))
        if group is None:
            break
        scopes.append(group)
        idx += 1
    return unique_id, eduperson_entitlement, scopes, issuer, audience


def parse_jwt(jwt_string):
    jwt = json.loads(jwt_string)
    unique_id = ""
    issuer = ""
    audience = ""
    scopes = []
    eduperson_entitlement = []
    if "voperson_id" in jwt:
        unique_id = jwt["voperson_id"]
    elif "sub" in jwt:
        unique_id = jwt["sub"]
    if "iss" in jwt:
        issuer = jwt["iss"]
    if "aud" in jwt:
        audience = jwt["aud"]
    if "eduperson_entitlement" in jwt:
        eduperson_entitlement = jwt["eduperson_entitlement"]
    if "scope" in jwt:
        scopes = jwt["scope"].split()
    return unique_id, eduperson_entitlement, scopes, issuer, audience


def process_jwt(groups, scopes):
    entitlements = []
    if scopes and not groups:
        for item in scopes:
            if "eduperson_entitlement:" in item:
                entitlements.append(item.replace("eduperson_entitlement:", ""))
            # TEMP
            if "eduperson_entitlement_jwt:" in item:
                entitlements.append(item.replace("eduperson_entitlement_jwt:", ""))
        groups = entitlements

    idx = 0
    while idx < len(groups):
        os.environ["BEARER_TOKEN_0_GROUP_" + str(idx)] = groups[idx]
        idx += 1
    return groups


def map_user(user, rules, config_file_path):
    for rule in rules:
        if (
            (rules[rule]["unique_id"] == "*" or user["unique_id"] == rules[rule]["unique_id"])
            and user["issuer"] == rules[rule]["issuer"]
            and (rules[rule]["audience"] == "*" or user["audience"] == rules[rule]["audience"])
            and (rules[rule]["scope"] == "*" or rules[rule]["scope"] in user["scopes"])
            and rules[rule]["group"] in user["groups"]
        ):
            sys.stdout.write(str(rule))
            sys.stdout.write("\n")
            sys.exit(0)
    log.error(
        "[egi-check-in-validator] Mapping user: Could not match identity based on config file: " + str(config_file_path)
    )
    sys.exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    rules, config_file_path = read_config_file(args)
    i, o, e = select.select([sys.stdin], [], [], TIMEOUT)
    if i:
        unique_id, entitlements, scopes, issuer, audience = parse_jwt(sys.stdin.readline().strip())
    else:
        unique_id, entitlements, scopes, issuer, audience = parse_env_variables()
    if entitlements or scopes:
        groups = process_jwt(entitlements, scopes)
    else:
        sys.exit(1)
    user = {
        "unique_id": unique_id,
        "issuer": issuer,
        "audience": audience,
        "scopes": scopes,
        "groups": groups,
    }
    map_user(user, rules, config_file_path)
