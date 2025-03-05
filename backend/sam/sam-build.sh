#!/bin/bash -xe

# Load environment variables from .env files
ENV_FILES=(
  "../.env"
  "../.env.development"
  "../.env.local"
)

# Source each env file if it exists
for file in "${ENV_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Loading environment from $file"
    set -a
    source "$file"
    set +a
  else
    echo "File $file not found (skipping)"
  fi
done

# Build with the exact parameter format SAM expects
sam build $1 --no-cached --use-container --parameter-overrides \
"ParameterKey=REGION_NAME,ParameterValue=${REGION_NAME:-us-east-1}" \
"ParameterKey=API_SECRETS_PARAM,ParameterValue=${API_SECRETS_PARAM}" \
"ParameterKey=PINECONE_ENV_PARAM,ParameterValue=${PINECONE_ENV_PARAM}" \
"ParameterKey=PINECONE_INDEX_PARAM,ParameterValue=${PINECONE_INDEX_PARAM}" \
"ParameterKey=COGNITO_USER_PARAM,ParameterValue=${COGNITO_USER_PARAM}" \
"ParameterKey=COGNITO_CLIENT_PARAM,ParameterValue=${COGNITO_CLIENT_PARAM}" \
"ParameterKey=INFRA_SECRETS_PARAM,ParameterValue=${INFRA_SECRETS_PARAM}" \
"ParameterKey=DYNAMODB_USER_TABLE_PARAM,ParameterValue=${DYNAMODB_USER_TABLE_PARAM}" \
"ParameterKey=S3_PROMPTS_BUCKET,ParameterValue=${S3_PROMPTS_BUCKET}" \

build_status=$?
if [ $build_status -eq 0 ]; then
  echo "SAM build completed successfully!"
else
  echo "SAM build failed with status $build_status"
fi
