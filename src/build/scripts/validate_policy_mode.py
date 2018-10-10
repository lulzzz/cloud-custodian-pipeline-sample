import yaml
import sys
import json

json_file = open(sys.argv[1])
policy_files = json.loads(json_file.read())['files']
for policy_file in policy_files:
    with open(policy_file) as stream:
        valid = True
        try:
            policies = yaml.load(stream)['policies']
            for policy in policies:
                if 'mode' not in policy.keys(
                ) or 'type' not in policy['mode'].keys(
                ) or policy['mode']['type'] != 'azure-periodic':
                    valid = False
            print(valid)
        except yaml.YAMLError as  exc:
            valid = False
            print(exc)