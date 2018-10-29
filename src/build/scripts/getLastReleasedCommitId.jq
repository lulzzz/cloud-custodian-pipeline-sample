[
.value[] |
.environments = ([
  # filter on successful releases
  .environments[] | select(.status == "succeeded")
])
# get the most recent release
] | max_by(.environments[].deploySteps[].queuedOn)
# get the commit id associated with the release
| .artifacts[].definitionReference.pullRequestMergeCommitId.id