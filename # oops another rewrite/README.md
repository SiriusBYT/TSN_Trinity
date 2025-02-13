# Sirio-Network API: Trinity
Raw/Websockets Relay Server for TSN written in Python in which it forwards requests to Back-End SN-APIs.

This server receives requests via Raw Sockets or Websockets with the Syntax "<code>[API]://[Request]</code>".
An example of a valid request would be "<code>FC-API://GET/MODULES</code>". Trinity does not care what is included in the "Request" section, it only sends whatever is contained inside to one of the back-end servers via raw sockets. *This API aims to solve the problem of **EACH API** needing **TWO** dedicated subdomains*.

It also removes the chaos of having to listen for websockets and raw sockets for each back-end api. This however obviously comes at the cost which is there is only a single failure point to bring the entire Sirio Network API down; assuming only one instance of this front-end server is ran.

# The Trinity API is currently unfinished and probably not very secure
I'd seriously advise not running this yet.

## Documentation will be later available.

