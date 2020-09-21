#!/usr/bin/env bash

set -e

PROJECT_NAME="cuphd-health-status-service"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "${GIT_BRANCH}" = "master" ]]; then
    VERSION=${VERSION:-"$(git describe --abbrev=0 --tags)"}
else
    VERSION=${VERSION:-"$(git rev-parse --abbrev-ref HEAD)"}
fi

aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 779619664536.dkr.ecr.us-east-2.amazonaws.com

docker build -f Dockerfile -t ${PROJECT_NAME}:${VERSION} .
docker tag ${PROJECT_NAME}:${VERSION} 779619664536.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:${VERSION}
docker push 779619664536.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:${VERSION}
