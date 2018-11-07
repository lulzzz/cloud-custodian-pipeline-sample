import getopt
import json
import subprocess
import sys
import os
import base64

class PolicyRunner(object):
    def __init__(self, config_file, policies_file, release_sp_secret_encoded, function_sp_secret_encoded, output_dir):
        with open(config_file) as f:
            self.config = json.load(f)
        with open(policies_file) as f:
            self.policies_config = json.load(f)

        try:
            release_sp_secret = base64.b64decode(release_sp_secret_encoded)
        except Exception:
            raise Exception('Failed to decode release service principal secret.')

        try:
            function_sp_secret = base64.b64decode(function_sp_secret_encoded)
        except Exception:
            raise Exception('Failed to decode function service principal secret.')

        try:
            self.release_sp_secret = json.loads(release_sp_secret)
        except Exception:
            raise Exception('Failed to load release service principal secret JSON.')

        try:
            self.function_sp_secret = json.loads(function_sp_secret)
        except Exception:
            raise Exception('Failed to load function service principal secret JSON.')

        if not self.release_sp_secret['tenantId'] or not self.release_sp_secret['appId'] or not self.release_sp_secret['clientSecret']:
            raise Exception('Release service principal secret JSON should contain non empty tenantId, appId and clientSecret.')

        if not self.function_sp_secret['tenantId'] or not self.function_sp_secret['appId'] or not self.function_sp_secret['clientSecret']:
            raise Exception('Function service principal secret JSON should contain non empty tenantId, appId and clientSecret.')

        self.output_dir = output_dir

    def run(self, dry_run=False):
        subscription_id = self.config['subscription']
        for policy_subscription_id in self.config['policy-subscriptions']:
            for policy_file in self.policies_config['files']:
                self._run_policy(subscription_id, policy_subscription_id, policy_file, dry_run)

    def _run_policy(self, subscription_id, policy_subscription_id, policy_file, dry_run=False):
        cmd = 'custodian run --output-dir=%s %s' % (self.output_dir, policy_file)
        cmd = "{0}{1}".format(cmd, (' --dryrun' if dry_run else ''))

        env = dict(os.environ)
        env['AZURE_SUBSCRIPTION_ID'] = subscription_id
        env['AZURE_TENANT_ID'] = self.release_sp_secret['tenantId']
        env['AZURE_CLIENT_ID'] = self.release_sp_secret['appId']
        env['AZURE_CLIENT_SECRET'] = self.release_sp_secret['clientSecret']

        env['AZURE_FUNCTION_SUBSCRIPTION_ID'] = policy_subscription_id
        env['AZURE_FUNCTION_TENANT_ID'] = self.function_sp_secret['tenantId']
        env['AZURE_FUNCTION_CLIENT_ID'] = self.function_sp_secret['appId']
        env['AZURE_FUNCTION_CLIENT_SECRET'] = self.function_sp_secret['clientSecret']

        subprocess.call(cmd, shell=True, env=env)


if __name__ in "__main__":
    config_file = ''
    policies_file = ''
    output_folder = ''
    release_sp_secret_encoded = ''
    function_sp_secret_encoded = ''
    dry_run = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:p:s:f:o:", ['dryrun'])
    except getopt.GetoptError as err:
        print(err)
        print('policy_runner.py -c <configFile> -p <policiesFile> -s <releaseSpSecretEncoded> -f <functionSpSecretEncoded> -o <outputFolder')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('policy_runner.py -c <configFile> -p <policiesFile> -s <releaseSpSecretEncoded> -f <functionSpSecretEncoded> -o <outputFolder')
            print('Example: policy_runner.py -c policies/config.json -p policies/policies.build.json -s releaseSpSecretEncoded -f functionSpSecretEncoded -o output --dryrun')
            sys.exit()
        elif opt in ("-c"):
            config_file = arg
        elif opt in ("-p"):
            policies_file = arg
        elif opt in ("-s"):
            release_sp_secret_encoded = arg
        elif opt in ("-f"):
            function_sp_secret_encoded = arg
        elif opt in ("-o"):
            output_folder = arg
        elif opt in ("--dryrun"):
            dry_run = True

    runner = PolicyRunner(config_file, policies_file, release_sp_secret_encoded, function_sp_secret_encoded, output_folder)
    runner.run(dry_run=dry_run)
