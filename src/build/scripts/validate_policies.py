import getopt
import json
import os
import sys

class ValidatePolicies(object):
    def __init__(self, modified_path):
        self.modified_path = modified_path
    
    def run(self):
        self._run_validate_policies(self.modified_path)
    
    @staticmethod
    def _run_validate_policies(modified_path):
        cmd = 'custodian validate %s' % (modified_path)
        os.system(cmd)

if __name__ in "__main__":
    modified_path = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:")
    except getopt.GetoptError:
        print('validate_policies.py -m <pathto_modified.yml>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m"):
            modified_path = arg
        
        runner = ValidatePolicies(modified_path)
        runner.run()