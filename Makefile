PROJECT_NAME := video-sync-service

export PROJECT_NAME := ${PROJECT_NAME}

.PHONY: build docker-deploy-dev docker-deploy-test docker-deploy-prod

build: Dockerfile
	docker build -f Dockerfile -t ${PROJECT_NAME}:latest .

deploy: build
	aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 430229884637.dkr.ecr.us-east-2.amazonaws.com
	docker tag ${PROJECT_NAME}:latest 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:dev
	docker push 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:dev

up: build
	docker-compose up

down:
	docker-compose down
