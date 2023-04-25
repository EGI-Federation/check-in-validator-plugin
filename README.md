# check-in-validator-plugin

A plugin for checking if an Access Token issued by EGI Check-in is valid. This
plugin can be used by HTCondor-CE and ARC-CE.

## Installation

This plugin can be installed by downloading the rpm packages from the releases
or by using the source code. The source code should be used only for
development.

### Release

You can find all the available rpm packages in the
[releases](https://github.com/rciam/check-in-validator-plugin/releases).

### Source code (For development)

To install the plugin using source code, run the following commands:

```bash
git clone https://github.com/rciam/check-in-validator-plugin.git
cd check-in-validator-plugin
python check-in-validator-plugin.py
```

## Configuration

This section is covering how to configure the plugin. You will need to configure the plugin in 2 sides, which are:

1. Configure the configuration file of the plugin
1. Configure the plugin in ARC-CE/HTCondor-CE

### Plugin

The `egi-check-in-validator` plugin has it's own configuration file. Just copy
the example configuration file to the home directory, using the command:

```bash
cp example-egi-check-in-validator.ini ~/egi-check-in-validator.ini
```

Then, edit the configuration file and add the mapping for the users.
The format of the syntax, is described bellow:

```text
MAPPING=UNIQUE_IDENTIFIER ISSUER AUDIENCE SCOPE GROUP
```

Example:

```text
foo=xyz@egi.eu https://aai-dev.egi.eu/auth/realms/egi oidc-agent compute.create urn:mace:egi.eu:group:vo.token-integration.egi.eu:role=member#aai.egi.eu
```

To execute the script use the command:

```bash
python egi-check-in-validator.py -c ~/egi-check-in-validator.ini
```

Note: If the `-c` option is missing then the plugin will try to open the
`egi-check-in-validator.ini` file from the following paths:

1. `/etc/arc-ce.d/egi-check-in-validator.conf`
1. `/etc/condor-ce.d/egi-check-in-validator.conf`

If the configuration file does not exist in the above paths, then the script
will fail with the message:

```text
[egi-check-in-validator] ERROR: Parsing configuration: Configuration file was not found.
```

### HTCondor

Set up an HTCondor-CE configuration as usual, then install/update the condor
packages provided here. No update to the HTCondor-CE packages is needed.
For the simplest configuration, add the following line to
`/etc/condor-ce/mapfiles.d/10-scitokens.conf` (this assumes there’s only one
issuer of EGI Check-in tokens):

```text
SCITOKENS /^https:\/\/aai-dev.egi.eu\/auth\/realms\/egi,.*/ PLUGIN:*
```

Then, create a file under `/etc/condor-ce/config.d/` like this:

```text
SEC_SCITOKENS_ALLOW_FOREIGN_TOKENS=true
SEC_SCITOKENS_PLUGIN_NAMES=EGI-CHECK-IN-VALIDATOR
SEC_SCITOKENS_PLUGIN_EGI-CHECK-IN-VALIDATOR_COMMAND=$(LOCAL_DIR)/ egi-check-in-validator-0.1.0-1.src.rpm -c <PATH_TO_CONFIG_FILE>
```

## How the plugin works

The plugin is expecting as input the payload of the JWT as decoded json in
string format in order to validate the token. If the JWT will not be provided
via stdin within 5 seconds, then the plugin will use the environment variables
that HTCondor/ARC creates. After parsing the JWT, the plugin will create
environment variables for each group that the user in member of. The format of
the environment variables have the following format:

```text
BEARER_TOKEN_0_GROUP_*
```

### Example providing JWT via stdin

Example input:

```bash
$ python egi-check-in-validator.py -c ~/egi-check-in-validator.ini
Insert JWT: 
{"exp":1681213287,"iat":1681209687,"auth_time":1681209570,"jti":"92cfba6e-7c6b-4012-9f6c-2539ef1b76f6","iss":"https://aai-dev.egi.eu/auth/realms/egi","sub":"bf009c87cb04f0a69fb2cc98767147e5b7408bedaef07b70ef33ef777318e610@egi.eu","typ":"Bearer","azp":"myClientID","nonce":"c2651c777c2c888fcf8244c22b1bcb14","session_state":"515679aa-b818-4902-ae7f-49b198aa0661","scope":"openid offline_access eduperson_entitlement voperson_id eduperson_entitlement_jwt eduperson_entitlement_jwt:urn:mace:egi.eu:group:vo.example.org:role=member#aai.egi.eu profile email","sid":"515679aa-b818-4902-ae7f-49b198aa0661","voperson_id":"bf009c87cb04f0a69fb2cc98767147e5b7408bedaef07b70ef33ef777318e610@egi.eu","authenticating_authority":"https://idp.admin.grnet.gr/idp/shibboleth","eduperson_entitlement":["urn:mace:egi.eu:group:vo.example.org:role=member#aai.egi.eu"]}
0
```

Example output:

```text
BEARER_TOKEN_0_GROUP_0=urn:mace:egi.eu:group:vo.example.org:role=member#aai.egi.eu
```

### Example providing JWT via environment variables

Example input:

```bash
$ export BEARER_TOKEN_0_CLAIM_voperson_id_0=bf009c87cb04f0a69fb2cc98767147e5b7408bedaef07b70ef33ef777318e610@egi.eu
$ export BEARER_TOKEN_0_CLAIM_eduperson_entitlement_0=urn:mace:egi.eu:group:vo.example.org:role=member#aai.egi.eu
$ export BEARER_TOKEN_0_CLAIM_eduperson_entitlement_1=urn:mace:egi.eu:group:vo.example.org:role=manager#aai.egi.eu
$ export BEARER_TOKEN_0_SCOPE_0=openid
$ export BEARER_TOKEN_0_SCOPE_1=compute.modify
$ export BEARER_TOKEN_0_SCOPE_2=compute.create
$ export BEARER_TOKEN_0_SCOPE_3=compute.read
$ export BEARER_TOKEN_0_SCOPE_4=eduperson_entitlement
$ export BEARER_TOKEN_0_SCOPE_5=voperson_id
$ export BEARER_TOKEN_0_SCOPE_6=profile
$ export BEARER_TOKEN_0_SCOPE_7=email
$ python egi-check-in-validator.py -c ~/egi-check-in-validator.ini
Insert JWT:
0
```

Example output:

```text
BEARER_TOKEN_0_GROUP_0=urn:mace:egi.eu:group:vo.example.org:role=member#aai.egi.eu
BEARER_TOKEN_0_GROUP_1=urn:mace:egi.eu:group:vo.example.org:role=manager#aai.egi.eu
```
