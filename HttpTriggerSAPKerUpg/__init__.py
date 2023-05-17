import logging

import azure.functions as func

import paramiko

import os

import requests

from urlparse import urlparse

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

#    name = req.params.get('name')
#    if not name:
#        try:
#            req_body = req.get_json()
#        except ValueError:
#            pass
#        else:
#            name = req_body.get('name')
##    command = "df"

# Update the next three lines with your
# server's information

##    host = "10.0.0.7"
##    username = "demouser"
##    password = "Demo@pass123"

##    client = paramiko.client.SSHClient()
##    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
##    client.connect(host, username=username, password=password)
##    _stdin, _stdout,_stderr = client.exec_command("touch abc")
##    print(_stdout.read().decode())
##    name = _stdout.read().decode()
##    client.close()

    username = 'S0024203723'
    password = 'Voidmain@0'

    url = 'https://softwaredownloads.sap.com/file/0020000000098642022'
    filename = os.path.basename(urlparse(url).path)

    r = requests.get(url, auth=(username,password))

    if r.status_code == 200:
        with open(filename, 'wb') as out:
            for bits in r.iter_content():
                out.write(bits)

#    if name:
#        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
#    else:
    return func.HttpResponse(
        "This HTTP triggered function executed successfully",
        status_code=200
    )
