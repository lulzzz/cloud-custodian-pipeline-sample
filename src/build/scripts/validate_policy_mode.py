import getopt
import yaml
import json
import sys

class ValidatePolicyMode(object):
    def __init__(self, policies_path):
        self.policies_path = policies_path

    def run(self):
        self._run_validate_policies(self.policies_path)

    @staticmethod
    def _run_validate_policies(policies_path):
        with open(policies_path) as stream:
            policies = yaml.load(stream)['policies']
            for policy in policies:
                if 'mode' not in policy.keys(
                ) or 'type' not in policy['mode'].keys(
                ) or policy['mode']['type'] != 'azure-periodic':
                    raise Exception('Policy ' + policy['name'] + ' is not in the function mode.')


if __name__ in "__main__":
    policies_path = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:")
    except getopt.GetoptError:
        print('validate_policy_mode.py -m <pathto_poolicies.yml>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m"):
            policies_path = arg

        runner = ValidatePolicyMode(policies_path)
        runner.run()
