# cloud-custodian-pipeline-sample

This is a sample implementation of an end to end [Cloud Custodian](https://github.com/capitalone/cloud-custodian) deployment on Azure

## Overview

At a high level, this sample pipeline enables you to

* Author Cloud Custodian policies in a code-first, pull request driven way
* Validate policies using Azure Pipelines
  * Verify that policies are well-formed
  * See what resources will be impacted by a proposed policy change before rolling it out to production
* Deploy policies into production as Azure Functions
* Alert resource owners on policy violations
* Aggregate and visualize policy results

## [Setup Guide](docs/setup.md)

You'll need to do some one-time setup to configure security, CI/CD, the data processing pipeline, and the mailer used to notify resource owners of policy violations. After this is done, you can iterate on policy development in a safe and automated environment. Follow the [Setup Guide](docs/setup.md) to get started.

## [Builds](docs/build.md)

The sample uses an [Azure DevOps YAML-based build](https://docs.microsoft.com/en-us/azure/devops/pipelines/get-started-yaml?view=vsts) pointing to [azure-pipelines.yml](/azure-pipelines.yml). You will need to edit this file and replace variable values with values specific to your Azure subscription and environment. The build runs on pull requests to validate new policies and identify what resources will be affected by proposed changes. Check out the [Build](docs/build.md) docs for a deep dive on individual tasks.

## [Releases](docs/release.md)

Currently, Azure DevOps does not support YAML-based releases. You will need to follow our [Release](docs/release.md) docs to set up your deployment strategy.

## Visualization

## Security Considerations

The general assumption in this sample is that only trusted people can modify policies. [azure-pipelines.yml](azure-pipelines.yml) contains the build definition that will be executed automatically upon receiving a pull request. This means that whoever can send pull requests can execute arbitrary code and access the Service Principals stored in Key Vault - which have access to your Azure Subscriptions. **Do not accept pull request from untrusted people**.

If you want to have separate permission sets for people who can create policies and those who can manage subscriptions, you'll need to implement additional security measures. Possible solutions are: having an additional branch that doesn't execute dry run or moving pull request validation logic to a standalone service, see: [Customize and extend pull request workflows with pull request status](https://docs.microsoft.com/en-us/azure/devops/repos/git/pull-request-status).

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
