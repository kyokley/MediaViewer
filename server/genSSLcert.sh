#!/bin/bash

openssl genrsa -aes256 -out server.key 4096
openssl req -sha256 -new -key server.key -out server.csr
cp server.key server.key.org
openssl rsa -in server.key.org -out server.key
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

