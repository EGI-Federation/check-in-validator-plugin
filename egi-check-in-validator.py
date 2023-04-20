import argparse
import json
import os
import select
import sys

# ISSUER = ""
UNIQUE_IDENTIFIER = ""
GROUPS = []
SCOPES = []
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
    # global ISSUER
    global UNIQUE_IDENTIFIER
    global GROUPS
    global SCOPES
    # ISSUER = os.getenv("BEARER_TOKEN_0_CLAIM_iss_0")
    unique_id = os.getenv("BEARER_TOKEN_0_CLAIM_voperson_id_0")
    if unique_id is None:
        unique_id = os.getenv("BEARER_TOKEN_0_CLAIM_sub_0")
    UNIQUE_IDENTIFIER = unique_id
    inx = 0
    eduperson_entitlement = []
    while True:
        group = os.getenv("BEARER_TOKEN_0_CLAIM_eduperson_entitlement_" + str(inx))
        if group is None:
            break
        eduperson_entitlement.append(group)
        inx += 1
    GROUPS = eduperson_entitlement
    inx = 0
    scopes = []
    while True:
        group = os.getenv("BEARER_TOKEN_0_SCOPE_" + str(inx))
        if group is None:
            break
        scopes.append(group)
        inx += 1
    SCOPES = scopes


def parse_jwt(jwt_string):
    # global ISSUER
    global UNIQUE_IDENTIFIER
    global GROUPS
    global SCOPES
    jwt = json.loads(jwt_string)
    # ISSUER = jwt["iss"]
    unique_id = ""
    if "voperson_id" in jwt:
        unique_id = jwt["voperson_id"]
    elif "sub" in jwt:
        unique_id = jwt["sub"]
    UNIQUE_IDENTIFIER = unique_id
    if "eduperson_entitlement" in jwt:
        GROUPS = jwt["eduperson_entitlement"]
    if "scope" in jwt:
        SCOPES = jwt["scope"].split()


def process_jwt():
    global GROUPS
    global SCOPES

    entitlements = []
    if SCOPES and not GROUPS:
        for item in SCOPES:
            if "eduperson_entitlement:" in item:
                entitlements.append(item.replace("eduperson_entitlement:", ""))
            # TEMP
            if "eduperson_entitlement_jwt:" in item:
                entitlements.append(item.replace("eduperson_entitlement_jwt:", ""))
        GROUPS = entitlements

    inx = 0
    while inx < len(GROUPS):
        os.environ["BEARER_TOKEN_0_GROUP_" + str(inx)] = GROUPS[inx]
        inx += 1
    sys.exit(0)


if __name__ == "__main__":
    args = parse_arguments()
    read_config_file(args)
    print("Insert JWT: ")
    i, o, e = select.select([sys.stdin], [], [], TIMEOUT)
    if i:
        parse_jwt(sys.stdin.readline().strip())
    else:
        parse_env_variables()
    if GROUPS or SCOPES:
        process_jwt()
    else:
        sys.exit(1)
