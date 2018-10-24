import getopt
import yaml
import sys
import os

class Policies(object):
    def __init__(self, policy_root, output_path):
        self.policy_root = policy_root
        self.output_path = os.path.join(os.getcwd(), output_path)

    def get_all(self):
        policies = self._get_combined_policies()
        output = {"policies": policies}
        with open(self.output_path, 'w') as output_file:
            print('\nWriting combined policies to:', self.output_path)
            yaml.dump(output, output_file)
    
    def _get_combined_policies(self):
        combined = []
        print('Gathering policies:')
        for dirpath, dirnames, filenames in os.walk(self.policy_root):
            for path in filenames:                
                full_path = os.path.join(os.getcwd(), dirpath, path)
                abs_path = os.path.abspath(full_path)
                if abs_path == self.output_path:
                    continue

                policies = Policies.get_policies(abs_path)
                for p in policies:
                    combined.append(p)
                    print(abs_path)
        return combined

    
    @staticmethod
    def get_policies(path):
        if path.endswith('.yaml') or path.endswith('.yml'):
            with open(path, 'r') as stream:
                data = yaml.safe_load(stream)
                if 'policies' in data:
                    return data['policies']
        return []


def show_help_and_exit():
    print('Usage: get_all_policies.py -r <root folder where policies are stored> -o <combined_output_path>')
    sys.exit(2)


if __name__ in "__main__":
    policy_root = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "r:o:")
    except getopt.GetoptError:
        show_help_and_exit()
    for opt, arg in opts:
        if opt in ("-r"):
            policy_root = arg
        elif opt in ("-o"):
            output_file = arg
    
    if not policy_root:
        show_help_and_exit()
    if not output_file:
        show_help_and_exit()

    policies = Policies(policy_root, output_file)
    policies.get_all()
