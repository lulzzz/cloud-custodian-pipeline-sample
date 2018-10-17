import getopt
import json
import subprocess
import sys
import os
import base64

class PolicyRunner(object):
    def __init__(self, config_file, policies_file, sp_secret_encoded, output_dir):
        with open(config_file) as f:
            self.config = json.load(f)
        with open(policies_file) as f:
            self.policies_config = json.load(f)
        
        try:
            sp_secret = base64.b64decode(sp_secret_encoded)
        except Exception:
            raise Exception('Failed to decode service principal secret.')
        
        try:
            self.sp_secret = json.loads(sp_secret)
        except Exception:
            raise Exception('Failed to load service principal secret JSON.')
        
        if not self.sp_secret['tenantId'] or not self.sp_secret['appId'] or not self.sp_secret['clientSecret']:
            raise Exception('Service principal secret JSON should contain non empty tenantId, appId and clientSecret.')
        
        self.output_dir = output_dir

    def run(self, dry_run=False):
        for subscription_id in self.config['subscriptions']:
            for policy_file in self.policies_config['files']:
                self._run_policy(subscription_id, policy_file, dry_run)

    def _run_policy(self, subscription_id, policy_file, dry_run=False):
        cmd = 'custodian run --output-dir=%s %s' % (self.output_dir, policy_file)
        cmd = "{0}{1}".format(cmd, (' --dryrun' if dry_run else ''))

        env = dict(os.environ)
        env['AZURE_TENANT_ID'] = self.sp_secret['tenantId']
        env['AZURE_SUBSCRIPTION_ID'] = subscription_id
        env['AZURE_CLIENT_ID'] = self.sp_secret['appId']
        env['AZURE_CLIENT_SECRET'] = self.sp_secret['clientSecret']

        subprocess.call(cmd, shell=True, env=env)


if __name__ in "__main__":
    config_file = ''
    policies_file = ''
    output_folder = ''
    sp_secret_encoded = ''
    dry_run = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:p:s:o:", ['dryrun'])
    except getopt.GetoptError:
        print('policy_runner.py -c <configFile> -p <policiesFile> -s <spSecretEncoded> -o <outputFolder')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('policy_runner.py -c <configFile> -p <policiesFile> -s <spSecretEncoded> -o <outputFolder')
            print('Example: policy_runner.py -c policies/config.json -p policies/policies.build.json -s spSecretEncoded -o output --dryrun')
            sys.exit()
        elif opt in ("-c"):
            config_file = arg
        elif opt in ("-p"):
            policies_file = arg
        elif opt in ("-s"):
            sp_secret_encoded = arg
        elif opt in ("-o"):
            output_folder = arg
        elif opt in ("--dryrun"):
            dry_run = True

    runner = PolicyRunner(config_file, policies_file, sp_secret_encoded, output_folder)
    runner.run(dry_run=dry_run)
