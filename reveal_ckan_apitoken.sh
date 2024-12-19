kubectl --context arn:aws:eks:eu-central-1:864823669523:cluster/klms_test -n stelar-dev get secrets ckan-admin-token-secret -o json | jq '.data | map_values(@base64d)'
