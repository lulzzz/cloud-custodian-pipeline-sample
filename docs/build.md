# Build design

## Build Tasks

### Installing Cloud Custodian
Typically Cloud Custodian for Azure is installed by installing the [`c7n`](https://pypi.org/project/c7n/) and [`c7n_azure`](https://pypi.org/project/c7n_azure/) PyPI packages. Instead of installing the packages, the build task is installing from a branch with workarounds to make unique storage accounts. There are several required changes that need to be in the PyPI packages for this pipeline to work as intended. When those changes are in the latests PyPI packages it is recommended to install those packages and not a specific Github branch. 

Tracking changes:
 * [Be able to specify a storage account](https://github.com/capitalone/cloud-custodian/pull/2955)

Installing Cloud Custodian is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Installing Cloud Custodian's PolicyStream Tool
The Cloud Custodian policystream.py tool is fetched from Cloud Custodian's [tools/ops/policystream.py](https://raw.githubusercontent.com/capitalone/cloud-custodian/master/tools/ops/policystream.py)

The prerequisities for using the tool requires pygit2. The package of pygit2 requires libgit2, installing these on Ubuntu requires the steps in
this [document](https://www.pygit2.org/install.html#quick-install).

Installing the policystream.py file and its prerequisites are triggered as Pipeline Build tasks in [azure-pipelines.yml](azure-pipelines.yml)

### Get Modifications to Custodian Policies
All modified Cloud Custodian policies are discovered by running the policystream.py script installed from Cloud Custodian. The command checks the difference between the master branch of a repository and the source branch. The tool outputs to a policies.yml file that contains all the new or modified policies in one yml file. 

Getting Custodian policy modifications is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

> Note: Policies must currently be placed at the root of the repository until [cloud-custodian/pull/2977](https://github.com/capitalone/cloud-custodian/pull/2977) is merged

### Cloud Custodian Policy Validation
All modified Cloud Custodian policies are linted and validated using the "custodian validate" command. 

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Policy Mode Validation
All Cloud Custodian policies should be in policy mode (type: azure-periodic). 

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

Policy validation is executed in [validate_policy_mode.py](src/build/scripts/validate_policy_mode.py)

### Cloud Custodian Dry run
After policy validation the pipeline executes a dry run of the modified policies.   

A diff is run on all modified policies and a policies.yml file is created.  The dry run executes against this policies.yml.  

The dry run will execute against the given subscription(s) but without taking action.  This shows what Cloud Custodian will execute in production.

The output of this dry run is then posted back to the PR as a comment.


## Security

The pipeline uses three Service Principals to access Azure:

* **CustodianBuildServicePrincipal**: used when a new pull request is submitted, to run Cloud Custodian policies in `--dry-run` mode, so that policy authors can see what resources will be affected by a change. This SP should be granted a limited role like `Reader`. These credentials are stored securely in Key Vault.

* **CustodianReleaseServicePrincipal**: used at runtime by Cloud Custodian to access Azure API's. This SP needs access to execute policies across your targeted subscriptions. If your policies modify resources, such as by adding tags or stopping VMs, this SP will need a role like `Contributor`. These credentials are stored securely in Key Vault.

* **Azure DevOps Service Connection**: used by Azure Pipelines to retrieve the other credentials from Key Vault and inject them as part of Build and Release. These credentials are automatically generated and managed by Azure DevOps.


> **Note**: Service Principal credentials stored in Key Vault are base64 encoded JSON in the following format: 
> ```
> {
>    "tenantId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", 
>    "appId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", 
>    "clientSecret": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
> }
> ```
