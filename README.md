# fakestun
Minimal/incomplete fake STUN server that always returns a static IP address. Written in a single Python file.

## Purpose
This script lacks many features of a real STUN server. Don't ever use it in a production environment. However, since this server allows you to quickly feed the client a fixed IP address of your choice, it can be useful for debugging your set-up (e.g. a SIP phone that has to run in a special environment like through VPNs or between several NATs). The server consists of a single file of standard Python, so it can be set up very quickly and runs on almost any system with a Python 3 environment.
