
docker-run-exchange:
	docker run -it -e GITW_CLIENTS="http://10.130.110.195:9000 http://10.130.110.195:9001" -v `pwd`/config.json:/var/has/gitw/config.json gitw-exchange
