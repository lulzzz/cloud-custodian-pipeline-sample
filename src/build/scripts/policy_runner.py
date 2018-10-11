import getopt
import json
import subprocess
import sys
import os

class PolicyRunner(object):
    def __init__(self, config_file, policies_file, sp_secret, output_dir):
        with open(config_file) as f:
            self.config = json.load(f)
        with open(policies_file) as f:
            self.policies_config = json.load(f)
        self.sp_secret = json.load(sp_secret)
        self.output_dir = output_dir

    def run(self, dry_run=False):
        for subscription_id in self.config['subscriptions']:
            for policy_file in self.policies_config['files']:
                self._run_policy(subscription_id, policy_file, dry_run)

    def _run_policy(self, subscription_id, policy_file, dry_run=False):
        cmd = 'custodian run --output-dir=%s %s' % (self.output_dir, policy_file)
        cmd = "{0}{1}".format(cmd, (' --dryrun' if dry_run else ''))

        env = dict(os.environ)
        env['AZURE_TENANT_ID'] = self.sp_secret['AZURE_TENANT_ID']
        env['AZURE_SUBSCRIPTION_ID'] = subscription_id
        env['AZURE_CLIENT_ID'] = self.sp_secret['AZURE_CLIENT_ID']
        env['AZURE_CLIENT_SECRET'] = self.sp_secret['AZURE_CLIENT_SECRET']

        subprocess.call(cmd, shell=True, env=env)


if __name__ in "__main__":
    config_file = ''
    policies_file = ''
    output_folder = ''
    sp_secret = ''
    dry_run = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:p:s:o:", ['dryrun'])
    except getopt.GetoptError:
        print('policy_runner.py -c <configFile> -p <policiesFile> -s <secretsFile> -o <outputFolder')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('policy_runner.py -c <configFile> -p <policiesFile> -s <secretsFile>   -o <outputFolder')
            print('Example: policy_runner.py -c policies/config.json -p policies/policies.json -s secret.sample.json -o output --dryrun')
            sys.exit()
        elif opt in ("-c"):
            config_file = arg
        elif opt in ("-p"):
            policies_file = arg
        elif opt in ("-s"):
            sp_secret = arg
        elif opt in ("-o"):
            output_folder = arg
        elif opt in ("--dryrun"):
            dry_run = True

    runner = PolicyRunner(config_file, policies_file, sp_secret, output_folder)
    runner.run(dry_run=dry_run)
