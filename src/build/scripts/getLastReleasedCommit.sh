#!/bin/bash
set -euo pipefail

main(){
  if [ "$#" -lt 5 ]; then
    cat << EOF
Usage: ./getLastReleasedCommit.sh ORG_URI PROJECT_NAME PROJECT_GUID BUILD_DEF_ID AZURE_DEVOPS_TOKEN

ORG_URI:              Uri of your Azure DevOps organization ie https://dev.azure.com/your_org.
                      Used to communicate with the Azure DevOps API
                      Azure DevOps Build variable: $(System.TeamFoundationCollectionUri)

PROJECT_NAME:         Name of your Azure DevOps project
                      Used to communicate with the Azure DevOps API
                      Azure DevOps Build variable: $(System.TeamProject)

PROJECT_GUID:         GUID ID of your Azure DevOps project
                      Used to find releases for a build definition
                      Azure DevOps Build variable: $(System.TeamProjectId)

BUILD_DEF_ID:         ID of your Azure DevOps build definition
                      Used to find releases for a build definition
                      Azure DevOps Build variable: $(System.DefinitionId)

AZURE_DEVOPS_TOKEN:   An Azure DevOps Bearer Token, used to query releases for a build.
                      Azure DevOps Build variable: $(System.AccessToken)
EOF
    exit 1
  fi

  ORG_URI=$1
  PROJECT_NAME=$2
  PROJECT_GUID=$3
  BUILD_DEF_ID=$4
  AZURE_DEVOPS_TOKEN=$5
  SOURCE_ID="$PROJECT_GUID:$BUILD_DEF_ID"
  AUTH_HEADER="Bearer $AZURE_DEVOPS_TOKEN"

  # Get organization name from ORG_URI
  # Examples:
  #   https://dev.azure.com/your_org
  #   https://your_org.visualstudio.com/
  ORG_NAME=""
  if [[ $ORG_URI =~ .*dev.azure.com* ]]
  then
    # Turns https://dev.azure.com/your_org into your_org
    ORG_NAME=${ORG_URI#https://dev.azure.com/}
    # Remove any trailing '/'
    ORG_NAME=${ORG_NAME%%/}
  elif [[ $ORG_URI =~ .*visualstudio.com* ]]
  then
    # Turns https://your_org.visualstudio.com into your_org.visualstudio.com
    ORG_NAME=${ORG_URI#https://}
    # Remove any trailing '/'
    ORG_NAME=${ORG_NAME%%/}
    # Turns your_org.visualstudio.com into your_org
    ORG_NAME=${ORG_NAME%.visualstudio.com}
  else
    echo "Unsupported Organization URL"
    exit 1
  fi

  URL="https://vsrm.dev.azure.com/$ORG_NAME/$PROJECT_NAME/_apis/release/releases?api-version=4.1-preview.6&sourceId=$SOURCE_ID&\$expand=environments,artifacts&queryOrder=descending"

  # URL encode
  URL=$(echo $URL | sed 's/ /%20/g' )
  RESPONSE_JSON=$(curl -s -X GET \
    "$URL" \
    -H "Authorization: $AUTH_HEADER" \
    -H "Cache-Control: no-cache")

  LAST_RELEASED_COMMIT_ID=$(echo $RESPONSE_JSON | jq -r -f ./src/build/scripts/getLastReleasedCommitId.jq)
  echo $LAST_RELEASED_COMMIT_ID
}

main "$@"