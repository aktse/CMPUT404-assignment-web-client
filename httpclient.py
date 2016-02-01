#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 Abram Hindle
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
import select
# you may use urllib to encode data appropriately
import urllib

def help():
    print "httpclient.py [GET/POST] [URL]\n"

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        # use sockets!
        so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = socket.gethostbyname(host)
        so.connect((ip, port))
        return so

    def get_code(self, data):
        # Status code
        code = data[0:20].split(" ")[1]
        return int(code)

    def get_headers(self,data):
        # Return everything before the empty line
        lines = data.splitlines(True)
        header = ""
        for line in lines:
            if line == "\n" or line == "\r\n":
                break
            else:
                header += line
        return header

    def get_body(self, data):
        # Return everything after the empty line
        lines = data.splitlines(True)
        body = ""
        found = False
        for line in lines:
            if line == "\n" or line == "\r\n":
                found = True
            elif found:
                body += line
        return body

    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)

    def parseGET(self, url):

        # Get hostname and port
        delim = ('/')
        start = url.find('://') + 3
        ending = len(url) 

        first = url.find(delim, start)     
        if first >= 0:                    
            ending = min(ending, first) 

        # Check if port is supplied
        if ':' in url[start:ending]:
            parsed = url[start:ending].rpartition(':')
            # host
            host = parsed[0]
            # port
            port = parsed[-1]
        else:
            # host 
            host = url[start:ending] 
            # Use https
            if 'https' in url:   
                port = 443
            else: # Use http 
                port = 80

        uri = url[ending:]
        # default URI
        if uri == '':
            uri = '/'

        return (host, int(port), uri)

    def parsePOST(self, url, args):

        (host, port, uri) = self.parseGET(url)
        # Process URI into uri and payload
        if isinstance(args, dict):
            payload = urllib.urlencode(args)
        else: # a string 
            s = uri.split('?')
            uri = s[0]
            # Payload was passed
            if len(s) > 1:
                payload = s[1]
            else: # No args
                payload = ""
        return (host, port, uri, payload)

    def GET(self, url, args=None):
        (host, port, uri) = self.parseGET(url)
        so = self.connect(host, port)
        # Make request
        so.send("GET %s HTTP/1.1\r\n" % uri)
        so.send("Host: %s \r\n" % host)
        so.send("Connection: close\r\n\r\n")
        data = self.recvall(so)
        code = self.get_code(data)
        body = self.get_body(data)
        so.close()
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        (host, port, uri, payload) = self.parsePOST(url, args)
        so = self.connect(host, port)
        # Make request
        so.send("POST %s HTTP/1.1\r\n" % uri)
        so.send("Host: %s\r\n" % host)
        so.send("Connection: close\r\n")
        so.send("Content-Type: application/x-www-form-urlencoded\r\n")
        so.send("Content-Length: %d\r\n\r\n" % len(payload))
        so.send(payload)
        data = self.recvall(so)
        code = self.get_code(data)
        body = self.get_body(data)
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print client.command( sys.argv[2], sys.argv[1] )
    else:
        print client.command( sys.argv[1] )   
