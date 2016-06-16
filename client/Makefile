

DOCKER_REPO_TAG_NAME = gitw-river-bidders

clean:
	sudo rm -fR __pycache__
	sudo rm -fR *.pyc

install: clean
	sudo python -m pip install --upgrade pip
	sudo python -m pip install --upgrade -r requirements.txt

docker-image: clean
	docker build -t $(DOCKER_REPO_TAG_NAME) .
	docker push $(DOCKER_REPO_TAG_NAME)