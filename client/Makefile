
DOCKER_REPO_TAG_NAME = gitw-river-bidders

clean:
	sudo rm -fR __pycache__
	sudo rm -fR *.pyc

install: clean
	sudo python -m pip install --upgrade pip
	sudo python -m pip install --upgrade -r requirements.txt

docker-list:
	docker ps

docker-kill:
	docker kill gitw-river-bidders
	docker rm gitw-river-bidders

docker-build: docker-kill
	docker build -t gitw-river-bidders .

docker-run-gitw-client:
	docker run -d -p 9001:80 -v `pwd`/dev_client.py:/usr/local/src/client/client.py gitw-client

docker-run:
	docker run --name gitw-river-bidders -d -p 9001:80 gitw-river-bidders
	docker ps
	docker logs -f gitw-river-bidders

docker-logs:
	docker logs -f gitw-river-bidders
