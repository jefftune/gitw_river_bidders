
DOCKER_REPO_TAG_NAME = gitw-river-bidders

clean:
	sudo rm -fR __pycache__
	sudo rm -fR *.pyc

install: clean
	sudo python -m pip install --upgrade pip
	sudo python -m pip install --upgrade -r requirements.txt

docker-build-river-bidders:
	docker build -t $(DOCKER_REPO_TAG_NAME) .

docker-run-gitw-client:
	docker run -d -p 9001:80 -v `pwd`/dev_client.py:/usr/local/src/client/client.py gitw-client

docker-run-gitw-river-bidders:
	docker run -d -p 9001:80 -v `pwd`/dev_client.py:/usr/local/src/client/client.py $(DOCKER_REPO_TAG_NAME)