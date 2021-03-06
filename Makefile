
DOCKER_REPO_TAG_NAME = gitw-river-bidders

docker-copy:
	scp -i ~/.ssh/GITW.pem -r ./client centos@10.130.110.195:
	scp -i ~/.ssh/GITW.pem -r Makefile centos@10.130.110.195:
	ssh -i ~/.ssh/GITW.pem centos@10.130.110.195

docker-access:
	ssh -i ~/.ssh/GITW.pem centos@10.130.110.195

docker-run-exchange:
	docker run -it -e GITW_CLIENTS="http://10.130.110.195:9001" -v `pwd`/config.json:/var/has/gitw/config.json gitw-exchange

docker-list:
	docker ps