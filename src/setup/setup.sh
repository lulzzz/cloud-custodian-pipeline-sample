#!/bin/bash
set -euo pipefail

main(){

  if [ "$#" -lt 3 ]; then
    cat << EOF
Usage: ./setup.sh CUSTODIAN_RG PIPELINE_SP (LOCATION)

CUSTODIAN_RG:   The name of the resource group to deploy resources into. If it does not exist, it will be created.

PIPELINE_SP:    The appId of the Service Principal used by the pipeline to retrieve secrets from Key Vault.
                You can find this by navigating to [Project settings] > [Pipelines] > Service connections]
                Select your service connection, and then choose [Manage Service Principal]

SENDGRID_PASS:  The password used to setup and access the SendGrid Email Service Azure resource.

LOCATION:     (Optional) The location of the Resource Group. Defaults to westus2
EOF
    exit 1
  fi

  CUSTODIAN_RG=$1
  PIPELINE_SP=$2
  SENDGRID_PASS=$3
  LOCATION=${4-westus2}
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
  az keyvault secret set --vault-name $VAULT -n SendGridPassword --description "SendGrid" --value $SENDGRID_PASS > /dev/null

  # Create Service Principals
  # - build: used to dry run PR's
  # - release: used to deploy policies as Azure Functions
  # - function: used to execute policies inside Azure Functions
  echo -e "Creating Service Principals\n"
  create_sp CustodianBuildServicePrincipal $VAULT
  create_sp CustodianReleaseServicePrincipal $VAULT
  create_sp CustodianFunctionServicePrincipal $VAULT
  log  "You will need to assign the appropriate permissions to allow Service Principals to have access to your subscription(s)."
  log "CustodianBuildServicePrincipal should have the 'Reader' role assigned to the subscription(s) where dry-run policies are ran against"
  log "CustodianReleaseServicePrincipal should have the 'Contributor' role assigned to the subscription(s) where policies are deployed to"
  log "CustodianFunctionServicePrincipal should have the 'Reader' role assigned to the subscription(s) where policies are ran against"
  log "CustodianFunctionServicePrincipal should have the 'Storage Blob Data Contributor' role assigned to the '$STORAGE_ACCT' storage account where policies will write logs to"
  log "CustodianFunctionServicePrincipal should have the 'Storage Queue Data Contributor' role assigned to the '$STORAGE_ACCT' storage account where policies with notifications will queue messages"
  log "If you plan to run policies with actions, CustodianFunctionServicePrincipal should have the 'Contributor' role or role(s) with enough permissions assigned to the subscription(s) where policies are ran against"
  log "You can do this via the portal or by using the CLI."
  log "Ex: 'az role assignment create --role Reader --assignee 00000000-0000-0000-0000-000000000000'"
}

# Create a Service Principal, format it for the CI/CD pipeline, and place it into Key Vault
create_sp(){
  # Generate a random suffix to avoid name collisions within the same AAD tenant
  local SP_NAME="$1"
  local SP_NAME_RANDOM="$SP_NAME-$RANDOM"
  local KEY_VAULT="$2"
  local SP=$(az ad sp create-for-rbac -n $SP_NAME_RANDOM --skip-assignment -o json)
  local SPID=$(echo $SP | jq -r .appId)
  local SECRET=$(echo $SP \
    | jq '{tenantId:.tenant,appId:.appId,clientSecret:.password}' \
    | base64)

  az keyvault secret set --vault-name $KEY_VAULT -n $SP_NAME -e base64 --description "Service Principal for Cloud Custodian" --value "$SECRET" > /dev/null

  log "Created Service Principal: $SP_NAME ($SPID)"
}

log(){
  echo "$(date +"%Y-%m-%d-%T") - $1" | tee -a setup.log
}

main "$@"
