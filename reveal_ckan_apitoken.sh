kubectl --context $1 get secrets ckan-admin-token-secret -o json | jq '.data | map_values(@base64d)'
