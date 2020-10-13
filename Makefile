PROJECT_NAME := play-service

export PROJECT_NAME := ${PROJECT_NAME}

.PHONY: build deploy

build: Dockerfile
	docker build -f Dockerfile -t ${PROJECT_NAME}:latest .

deploy: build
	aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 430229884637.dkr.ecr.us-east-2.amazonaws.com
	docker tag ${PROJECT_NAME}:latest 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:prod
	docker push 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:prod

up: build
	docker-compose up

down:
	docker-compose down

clean: down
	docker rm -f $(docker container ls -a | grep play-service | awk '{print $1}') 2>/dev/null || true
	docker rmi -f $(docker images | grep play-service | awk '{print $3}')

redeploy: deploy
	aws ecs update-service --cluster dti-play --service dti_play_service --force-new-deployment

