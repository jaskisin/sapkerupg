import logging

import azure.functions as func

import paramiko

import os

import requests

import httplib2

from suds.client import Client

from urllib.parse import urlparse

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobLeaseClient, BlobPrefix, ContentSettings

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
 #   url = 'https://softwaredownloads.sap.com/file/0020000000098642022'
 #   user = 'S0024203723'
 #   password = 'Voidmain@0'
 #   headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
 #   client = Client(url, username=user, password=password, headers=headers)
 #   result = client.service.GetFileContent('0020000000098642022')
 #   resp = requests.get(url, auth=(user, password),headers=headers,allow_redirects=True)
 #   http = httplib2.Http()
 #   http.add_credentials(user, password)
 #   content = http.request(url,headers=headers,method="GET",redirections=5)
 #   fd = open('C:\\Users\\jasksingh\\Documents\\0020000000098642022', 'wb')
 #   fd.write(result)
 #   fd.close()
    
    
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
##    _stdin, _stdout,_stderr = client.exec_command("touch abc")
##    print(_stdout.read().decode())
##    name = _stdout.read().decode()
##    client.close()
    accounturl = "https://jassapbits.blob.core.windows.net"
    container = "sapbits"
    cred="FtLah1vqmHzp7kqjeF6dykvdEOLIMMD9ZQt9xrq5ggrw6izE9u3otr+LHqkTf2bTSixN2BXtArWU+AStxlCpPw=="
    blob_name = "S4HANA_2021_ISS_v0001ms.yaml"
    filepath = "/tmp/"
    filename = "S4HANA_2021_ISS_v0001ms.yaml"
# Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(accounturl,cred)

    def download_blob_to_file(self, blob_service_client: BlobServiceClient, container_name):
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        with open(file=os.path.join(filepath, filename), mode="wb") as sample_blob:
            download_stream = blob_client.download_blob()
            sample_blob.write(download_stream.readall())
    
    def sap_operation(host,instancenumber, osuser, ospass, operation):
        url = "http://"+host+":5"+instancenumber+"13?wsdl"
        client = Client(url, username=osuser, password=ospass)
        result = client.service.GetProcessList()
        print(result)
    
    opt = sap_operation("10.0.0.7","00", "ts3adm", "Demo@pass123", "GetProcessList")
    
    download_blob_to_file(any,blob_service_client, container)
    host = "10.0.0.7"
    username = "demouser"
    password = "Demo@pass123"
    localpath = "/tmp/S4HANA_2021_ISS_v0001ms.yaml"
    remotepath = "/tmp/S4HANA_2021_ISS_v0001ms.yaml"
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    sftp = client.open_sftp()
    sftp.put(localpath, remotepath)
    sftp.close()
    client.close()
#    if name:
#        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
#    else:
    return func.HttpResponse(
        "This HTTP triggered function executed successfully",
        status_code=200
    )
