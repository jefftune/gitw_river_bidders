
## RIVER BIDDERS

```bash
# start the sample client
$ cd ~
$ scp -i ~/.ssh/GITW.pem ~/GITW2016/gitw-client.tar.gz centos@10.130.110.195:
$ ssh -i ~/.ssh/GITW.pem centos@10.130.110.195
[centos@ip-10-130-110-XXX ~]$ zcat gitw-client.tar.gz | docker load
[centos@ip-10-130-110-XXX ~]$ docker run -d -p 9000:80 gitw-client
# congratulations, you're now qualified to enter the competition!
 
# start the test exchange server
$ scp -i ~/.ssh/GITW.pem ~/GITW2016/gitw-exchange.tar.gz centos@10.130.110.195:
$ scp -i ~/.ssh/GITW.pem ~/GITW2016/config.json centos@10.130.110.195:
$ ssh -i ~/.ssh/GITW.pem centos@10.130.110.195
[centos@ip-10-130-110-XXX ~]$ zcat gitw-exchange.tar.gz | docker load
[centos@ip-10-130-110-XXX ~]$ docker run -it -e GITW_CLIENTS="http://10.130.110.195:9000" -v `pwd`/config.json:/var/has/gitw/config.json gitw-exchange
# watch logs in this terminal to see auction results
 
# run a modified demo client with live reload
$ scp -i ~/.ssh/GITW.pem -r ~/GITW2016/client centos@10.130.110.195:
$ ssh -i ~/.ssh/GITW.pem centos@10.130.110.195
[centos@ip-10-130-110-XXX ~]$ cd client
[centos@ip-10-130-110-XXX client]$ cp client.py fixedclient.py
# modify fixedclient.py line 48 to bid 0.10 instead of random.random()
[centos@ip-10-130-110-XXX client]$ docker run -d -p 9001:80 -v `pwd`/fixedclient.py:/usr/local/src/client/client.py gitw-client
[centos@ip-10-130-110-XXX client]$ cd ..
[centos@ip-10-130-110-XXX ~]$ docker run -it -e GITW_CLIENTS="http://10.130.110.195:9000 http://10.130.110.195:9001" -v `pwd`/config.json:/var/has/gitw/config.json gitw-exchange
# modify fixedclient.py to bid 0.20 instead of 0.10, note live reload
```