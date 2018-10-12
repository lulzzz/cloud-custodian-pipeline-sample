import sys
import os
import getopt
from vsts.vss_connection import VssConnection
from msrest.authentication import BasicAuthentication
from vsts.git.v4_1.models import Comment
from vsts.git.v4_1.models.git_pull_request_comment_thread import GitPullRequestCommentThread

vso_task_skipped = "##vso[task.complete result=Skipped;]"
vso_task_succeeded = "##vso[task.complete result=Succeeded;]"
vso_task_log_error = "##vso[task.logissue type=error;]"
vso_task_log_warning = "##vso[task.logissue type=warning;]"


class PostToPr:

    def __init__(self, enable_vso_output):
        self.enable_vso_output = enable_vso_output

    def read_output(self, output_dir):
        print(f"Looking for output in: {output_dir}")
        output = ''
        for root, subdirs, files in os.walk(output_dir):
            for file in os.listdir(root):
                file_path = os.path.join(root, file)
                if os.path.isdir(file_path):
                    pass
                # if any files match the expected cloud custodian output read in and append to comment
                elif '-run.log' in file_path:
                    # parent_folder_name = file_path.split(os.pathsep)[-2]
                    with open(file_path) as src:
                        file_contents = src.read()
                        output += f"{root}\n"
                        if file_contents is not None and file_contents is not '':
                            output += f"{file_contents}\n"
                        else:
                            output += f"No output in the dry run of this policy\n\n"
        return output

    def post_output_to_pr(self, organization_uri, project, repo_id, pull_request_id, token, comment_content):
        if comment_content == '':
            print(f"{vso_task_skipped if self.enable_vso_output else ''}No Cloud Custodian output found in output dir")
            sys.exit()

        # Create a connection to the org
        credentials = BasicAuthentication('', token)
        connection = VssConnection(base_url=organization_uri, creds=credentials)

        # Get a git client
        git_client = connection.get_client("vsts.git.v4_1.git_client.GitClient")

        new_comment = Comment(content=comment_content)
        comments = [new_comment]
        comment_thread = GitPullRequestCommentThread(comments=comments)

        try:
            # Create a comment based on the cloud custodian output
            resp = git_client.create_thread(comment_thread, repo_id, pull_request_id, project)
            print(f"{vso_task_succeeded if self.enable_vso_output else ''}Successfully updated the pull request {pull_request_id}, the comment thread id is: {resp.id}")
        except Exception as e:
            print(f"{vso_task_skipped if self.enable_vso_output else ''}Unable to post comment to PR: {pull_request_id}, {e}")
            sys.exit(1)


if __name__ == '__main__':
    opt_organization_uri = ''
    opt_repo_id = ''
    opt_pull_request_id = ''
    opt_project = ''
    opt_azure_devops_token = ''
    opt_output_dir = ''
    enable_vso_output = False

    help_text = "post_to_pr.py -o <organization> -p <project> -r <repository id> -i <pull request id> -t <azure devops access token> -d <cloud custodian output dir> --enable-vso-output"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:o:p:r:i:t:d:", ['enable-vso-output'])
    except getopt.GetoptError:
        print(help_text)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(help_text)
            print('Example: post_to_pr.py -o https://dev.azure.com/myorg/ -p "myproject" -r "abc-123-def-456-hig-789" -i 123 -t "abcdef123456hijklm78910" -d "C:\\a\\b\\c\\output"')
            print('Azure Devops Example: post_to_pr.py -o contoso -p "myproject" -r "abc-123-def-456-hig-789" -i 123 -t "abcdef123456hijklm78910" -d "C:\\a\\b\\c\\output" --enable-vso-output')
            sys.exit()
        elif opt in "-o":
            opt_organization_uri = arg
        elif opt in "-p":
            opt_project = arg
        elif opt in "-r":
            opt_repo_id = arg
        elif opt in "-i":
            opt_pull_request_id = arg
        elif opt in "-t":
            opt_azure_devops_token = arg
        elif opt in "-d":
            opt_output_dir = arg
        elif opt in "--enable-vso-output":
            enable_vso_output = True

    post_to_pr = PostToPr(enable_vso_output)

    # Read Cloud Custodian output directory
    custodian_output = post_to_pr.read_output(opt_output_dir)

    # Optionally log a warning to the Azure DevOps CI
    if enable_vso_output and custodian_output == '':
        print(f"{vso_task_log_warning}No Cloud Custodian output found in output dir: {opt_output_dir}")

    # Post the cloud custodian output to the given PR
    post_to_pr.post_output_to_pr(
        opt_organization_uri,
        opt_project,
        opt_repo_id,
        opt_pull_request_id,
        opt_azure_devops_token,
        custodian_output
    )
