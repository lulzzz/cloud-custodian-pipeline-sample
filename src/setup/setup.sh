#!/bin/bash
set -euo pipefail

main(){

  if [ "$#" -lt 4 ]; then
    cat << EOF
Usage: ./setup.sh CUSTODIAN_RG PIPELINE_SP PAT (LOCATION)

CUSTODIAN_RG:   The name of the resource group to deploy resources into. If it does not exist, it will be created.

PIPELINE_SP:    The appId of the Service Principal used by the pipeline to retrieve secrets from Key Vault.
                You can find this by navigating to [Project settings] > [Pipelines] > Service connections]
                Select your service connection, and then choose [Manage Service Principal]

PAT:            An Azure DevOps Personal Access Token, used to post feedback to pull requests. This will be stored
                securely inside Key Vault

SENDGRID_PASS:  The password used to setup and access the SendGrid Email Service Azure resource.

LOCATION:     (Optional) The location of the Resource Group. Defaults to westus2
EOF
    exit 1
  fi

  CUSTODIAN_RG=$1
  PIPELINE_SP=$2
  PAT=$3
  SENDGRID_PASS=$4
  LOCATION=${5-westus2}
  MAILQUEUE_NAME=mailqueue

  # Translate the Service Principal appId into an objectId
  PIPELINE_SP_OID=$(az ad sp list --spn $PIPELINE_SP --query '[0].objectId' -o tsv)

  # Create the infrastructure resources needed to create an environment
  echo "Deploying resources to $CUSTODIAN_RG"
  az group create -n $CUSTODIAN_RG -l $LOCATION > /dev/null
  DEPLOYMENT=$(az group deployment create -g $CUSTODIAN_RG --template-file templates/azuredeploy.json --parameters pipelineServicePrincipalObjectId=$PIPELINE_SP_OID sendGridPassword=$SENDGRID_PASS -o json)
  STORAGE_ACCT=$(echo $DEPLOYMENT | jq -r .properties.outputs.storageAccountName.value)
  VAULT=$(echo $DEPLOYMENT | jq -r .properties.outputs.keyVaultName.value)
  az storage queue create --name $MAILQUEUE_NAME --account-name $STORAGE_ACCT > /dev/null

  log "Storage account for Cloud Custodian logs created: $STORAGE_ACCT"
  log "Key Vault for pipelines created: $VAULT"
  log "Storage queue for Cloud Custodian mailer created: https://$STORAGE_ACCT.queue.core.windows.net/$MAILQUEUE_NAME"

  # Add permissions to allow setting Key Vault secrets
  az keyvault set-policy -n $VAULT --upn $(az account show --query 'user.name' -o tsv) --secret-permissions get list set delete backup restore recover > /dev/null

  # Add secrets to Key Vault
  az keyvault secret set --vault-name $VAULT -n AzureDevOpsApiToken --description "Azure DevOps PAT token" --value $PAT > /dev/null
  az keyvault secret set --vault-name $VAULT -n SendGridPassword --description "SendGrid" --value $SENDGRID_PASS > /dev/null

  # Create Service Principals
  # - build: used to dry run PR's
  # - release: used to execute policies inside Azure Functions
  echo -e "Creating Service Principals\n"
  create_sp CustodianBuildServicePrincipal $VAULT
  create_sp CustodianReleaseServicePrincipal $VAULT
  echo -e  "\nYou will need to assign the appropriate permissions to allow Service Principals to have access to your subscription(s)."
  echo "You can do this via the portal or by using the CLI."
  echo "Ex: 'az role assignment create --role Reader --assignee 00000000-0000-0000-0000-000000000000'"
}

# Create a Service Principal, format it for the CI/CD pipeline, and place it into Key Vault
create_sp(){
  # Generate a random suffix to avoid name collisions within the same AAD tenant
  local SP_NAME="$1-$RANDOM"
  local SP=$(az ad sp create-for-rbac -n $SP_NAME --skip-assignment -o json)
  local SPID=$(echo $SP | jq -r .appId)
  local SECRET=$(echo $SP \
    | jq '{tenantId:.tenant,appId:.appId,clientSecret:.password}' \
    | base64)

  az keyvault secret set --vault-name $2 -n $1 -e base64 --description "Service Principal for Cloud Custodian" --value "$SECRET" > /dev/null

  log "Created Service Principal: $SP_NAME ($SPID)"
}

log(){
  echo "$(date +"%Y-%m-%d-%T") - $1" | tee -a setup.log
}

main "$@"
