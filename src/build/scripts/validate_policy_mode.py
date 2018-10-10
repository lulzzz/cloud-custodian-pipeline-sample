import getopt
import yaml
import json
import sys

class ValidatePolicies(object):
    def __init__(self, modified_path):
        self.modified_path = modified_path
    
    def run(self):
        self._run_validate_policies(self.modified_path)
    
    @staticmethod
    def _run_validate_policies(modified_path):
        with open(modified_path) as stream:
            policies = yaml.load(stream)['policies']
            for policy in policies:
                if 'mode' not in policy.keys(
                ) or 'type' not in policy['mode'].keys(
                ) or policy['mode']['type'] != 'azure-periodic':
                    raise Exception('Policy '+ policy['name'] + ' is not in the function mode.')

if __name__ in "__main__":
    modified_path = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:")
    except getopt.GetoptError:
        print('validate_policy_mode.py -m <pathto_modified.yml>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m"):
            modified_path = arg
        
        runner = ValidatePolicies(modified_path)
        runner.run()           