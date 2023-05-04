import argparse
import configparser
import json
import os
import select
import sys

TIMEOUT = 5
CONFIG_PATHS = [
    "/etc/arc-ce/config.d/egi-check-in-validator.conf",
    "/etc/condor-ce/config.d/egi-check-in-validator.conf",
]


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="path of the configuration file.")
    args = parser.parse_args()
    return vars(args)


def read_config_file(arguments):
    global CONFIG_PATHS
    filename = None
    paths = [arguments["config"]] + CONFIG_PATHS
    for path in paths:
        if path and os.path.exists(path):
            filename = path
    if not filename:
        sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
        sys.stderr.write("Configuration file was not found.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(filename)
    mappings = {}
    for key, value in config.items("mappings"):
        value = value.rstrip()
        line = value.split(" ")
        if len(line) == 5:
            if line[1] == "*":
                sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
                sys.stderr.write('"{}" Mapper: ISSUER cannot be "*". Please enter a valid value.'.format(key))
                sys.exit(1)
            if line[4] == "*":
                sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
                sys.stderr.write('"{}" Mapper: GROUP cannot be "*". Please enter a valid value.'.format(key))
                sys.exit(1)
        else:
            sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
            sys.stderr.write('"{}" Mapper: invalid mapping configuration'.format(key))
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
    sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
    sys.stderr.write("Could not match identity based on config file: " + str(config_file_path))
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
