# cloud-custodian-pipeline-sample

This is a sample implementation of an end to end [Cloud Custodian](https://github.com/capitalone/cloud-custodian) deployment on Azure

## Prerequisites
* Docker

## Setup

You'll need to do some one-time setup to configure security, CI/CD, and the data processing pipeline. After this is done, you can iterate on policy development in a safe automated environment.


### Provisioning

A `Dockerfile` is provided for easy setup and configuration of Azure resources in a container, regardless if you are on Windows/Linux/Mac. All that is required is docker to build and run the docker container.
```
docker build -t cloud-custodian-pipeline:latest
docker run -it cloud-custodian-pipeline:latest
```

### Service Principals

You'll need two Service Principals.

* The first is used at runtime by Cloud Custodian to access to the Azure API's. This SP needs access to execute policies across your targeted Subscriptions.
Credentials of this service principal should be added to KeyVault as the following data structure:

{
   "tenantId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
   "appId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
   "clientSecret": "correct-horse-battery-staple"
 }

* The second is used at release time by the Azure DevOps pipeline. This SP needs access to pull secrets from a KeyVault.

## Policies

## Configuration
All target subscriptions should be listed in [config.json](policies/config.json)

## Build Tasks

### Installing Cloud Custodian's PolicyStream Tool
The Cloud Custodian policystream.py tool is fetched from Cloud Custodian's [tools/ops/policystream.py](https://raw.githubusercontent.com/capitalone/cloud-custodian/master/tools/ops/policystream.py)

The prerequisities for using the tool requires pygit2. The package of pygit2 requires libgit2, installing these on ubuntu requires the steps in
this [document.](https://www.pygit2.org/install.html#quick-install)

Installing the policystream.py file and its prerequisites are triggered as Pipeline Build tasks in [azure-pipelines.yml](azure-pipelines.yml)

### Get Modifications to Custodian Policies
All modified Cloud Custodian policies are discovered by running the policystream.py script installed from Cloud Custodian. The command checks the difference between the master branch of a repository and the source branch. The tool outputs to a modified.yml file that contains all the new or modified policies in one yml file. 

Getting Custodian policy modifications is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Cloud Custodian Policy Validation
All modified Cloud Custodian policies are linted and validated using the "custodian validate" command. 

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

### Policy Mode Validation
All Cloud Custodian policies should be in policy mode (type: azure-periodic). 

Policy validation is triggered as a Pipeline Build task in [azure-pipelines.yml](azure-pipelines.yml)

Policy validation is executed in [validate_policy_mode.py](src/build/scripts/validate_policy_mode.py)

# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
