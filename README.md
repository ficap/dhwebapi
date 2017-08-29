# Dockerhub Web API – Python library
This library helps you to easily interact with hub.docker.com **web** interface.
It's really up to you how you use it whether you use cli or make your own app based on this library. 
This library is only Python3 compatible. 
## Dependencies
* [python](https://www.python.org/)
* [requests](https://github.com/requests/requests)


## Possible use-cases:
1. **I need to periodically update description of my DH repo when there's a new build**
    * of course it's really simple
        * dh = DockerHubWebAPI(username, password)
        * dh.update_full_description(description)
    * or by using cli interface
        * dhwebapi 
        
2. great for use inside jenkins tasks
   
