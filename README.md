Before running commands please ensure you have the correct libraries installed.

You can do this by running this command in the directory of the script
````commandline
pip install -r requirements.txt
````
Once all libraries are installed and the server is up and running, you can get all running servers by running
````commandline
curl 0.0.0.0:<port>/status
````
or opening in your browser.
To access the average usage of each service, you can do so by running the curl command below.
````commandline
curl 0.0.0.0:<port>/services
````
and the following for service health
```commandline
curl 0.0.0.0:<port>/service-health
```
This returns the service along with ips of the servers