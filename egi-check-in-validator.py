import argparse
import json
import os
import select
import sys

TIMEOUT = 5
CONFIG_PATHS = [
    "/etc/condor-ce.d/egi-check-in-validator.conf"
    "/etc/arc-ce.d/egi-check-in-validator.conf"
]


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="path of the configuration file.")
    args = parser.parse_args()
    return vars(args)


def read_config_file(arguments):
    global CONFIG_PATHS
    filename = None
    if os.path.exists(arguments["config"]):
        filename = arguments["config"]
    else:
        for path in CONFIG_PATHS:
            if os.path.exists(path):
                filename = path
    if not filename:
        sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
        sys.stderr.write("Configuration file was not found.")
        sys.exit(1)

    with open(filename, "r") as conf_file:
        config = valid_lines(conf_file)
        for line in config:
            if len(line) == 7:
                if line[6] == "*":
                    sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
                    sys.stderr.write('Line {}: GROUP cannot be "*". Please enter a valid value.'.format(line[0]))
                    sys.exit(1)
            else:
                sys.stderr.write("[egi-check-in-validator] ERROR: Parsing configuration: ")
                sys.stderr.write("Line {}: invalid mapping configuration".format(line[0]))
                sys.exit(1)


def valid_lines(file):
    result = []
    for index, line in enumerate(file):
        line = line.rstrip()
        if line and not line.startswith("#"):
            # The rules will have the format:
            # LINE_NUMBER MAPPING SUBJECT ISSUER AUDIENCE SCOPE GROUP
            result.append([index + 1] + line.split(" "))
    return result


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


if __name__ == "__main__":
    args = parse_arguments()
    read_config_file(args)
    print("Insert JWT: ")
    i, o, e = select.select([sys.stdin], [], [], TIMEOUT)
    if i:
        unique_id, entitlements, scopes, issuer, audience = parse_jwt(sys.stdin.readline().strip())
    else:
        unique_id, entitlements, scopes, issuer, audience = parse_env_variables()
    if entitlements or scopes:
        groups = process_jwt(entitlements, scopes)
    else:
        sys.exit(1)
