# Build design

The build pipeline is setup to run on an Ubuntu Linux build agent and triggered to run each time a change is committed to the `master` branch. Typically, this is done when merging pull requests. All build variables are defined at the top of the pipeline under the `variables` group.

## Build Tasks

### Using Python version 3.6

Currently, Cloud Custodian is built and validated against Python 3.6.

### Download Azure Key Vault Secrets

For each build, secrets are downloaded securely from Azure Key Vault, stored in memory and only accessible to the current build.

### Installing Cloud Custodian

Cloud Custodian for Azure is installed by installing the [`c7n`](https://pypi.org/project/c7n/) and [`c7n_azure`](https://pypi.org/project/c7n_azure/) PyPI packages.

Installing Cloud Custodian is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Installing Cloud Custodian's PolicyStream Tool

The Cloud Custodian policystream python tool is fetched from [https://pypi.org/project/c7n-policystream/](https://pypi.org/project/c7n-policystream/). This tool is used in later build steps.

The prerequisities for using the tool requires pygit2. The package of pygit2 requires libgit2, installing these on Ubuntu requires the steps in
this [document](https://www.pygit2.org/install.html#quick-install).

Installing the c7n-policystream python tool and its prerequisites are triggered as Pipeline Build tasks in [azure-pipelines.yml](azure-pipelines.yml)

### Get Modifications to Custodian Policies (`validatePolicyChangesOnly: true`)

The default CI behavior is to run checks only on modified policies. All modified Cloud Custodian policies are discovered by running the c7n-policystream python tool installed from Cloud Custodian. The command checks the difference between the master branch of a repository and the source branch. The tool outputs to a policies.yml file that contains all the new or modified policies in one yml file.

Getting Custodian policy modifications is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

> This task is skipped when queuing a manual build to validate all policies.

> Note: Policies must currently be placed at the root of the repository until [cloud-custodian/pull/2977](https://github.com/capitalone/cloud-custodian/pull/2977) is merged

### Get All Custodian Policies (`validatePolicyChangesOnly: false`)

The build can optionally validate all policies in the repository. This is useful when making changes to the CI/CD pipeline itself and policies are not being touched. To run in this mode, queue a manual build and set `validatePolicyChangesOnly: false`.

> This task is skipped by default, when validating only modified policies.

### Cloud Custodian Policy Validation

Cloud Custodian policies are linted and validated using the `custodian validate` command.

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Policy Mode Validation

All Cloud Custodian policies should be in policy mode (type: azure-periodic).

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

Policy validation is executed in [validate_policy_mode.py](src/build/scripts/validate_policy_mode.py)

### Cloud Custodian Dry run

After policy validation the pipeline executes a dry run of the policies.

The dry run will execute against the given subscription(s) but without taking action.  This shows what Cloud Custodian will execute in production.

The output of this dry run is then posted back to the PR as a comment.

## Security

The pipeline uses four Service Principals to access Azure:

* **CustodianBuildServicePrincipal**: used when a new pull request is submitted, to run Cloud Custodian policies in `--dry-run` mode, so that policy authors can see what resources will be affected by a change. This SP should be granted a limited role like `Reader` on all subscriptions where policies will run against. These credentials are stored securely in Key Vault.

* **CustodianReleaseServicePrincipal**: used at release time to deploy policies to an Azure Subscription. This SP needs access to the subscription where policies will be deployed to and will need the role like `Contributor`. These credentials are stored securely in Key Vault.

* **CustodianFunctionServicePrincipal**: used at runtime by Cloud Custodian to access Azure API's. This SP needs access to execute policies across your targeted subscriptions. If your policies modify resources, such as by adding tags or stopping VMs, this SP will need a role like `Contributor`. If your policies only find and report on resources, this SP will need a role like `Reader`. This SP will also need the `Storage Blob Data Contributor` and `Storage Queue Data Contributor` roles on the storage account where policies logs are written to and notification messages are queued. These credentials are stored securely in Key Vault.

* **Azure DevOps Service Connection**: used by Azure Pipelines to retrieve the other credentials from Key Vault and inject them as part of Build and Release. These credentials are automatically generated and managed by Azure DevOps.

> **Note**: Service Principal credentials stored in Key Vault are base64 encoded JSON in the following format:
> ```json
> {
>    "tenantId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
>    "appId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
>    "clientSecret": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
> }
> ```
