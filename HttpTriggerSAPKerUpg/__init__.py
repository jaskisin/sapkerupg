import logging

import azure.functions as func

import paramiko

import os

import requests

import httplib2

import sapkerupg

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
    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        accountname = req_body.get('AccountName')
        container = req_body.get('Container')
        sascred = req_body.get('SASCred')
        sapexefile = req_body.get('SAPExeFile')
        sapcarfile = req_body.get('SAPCarFile')
        host = req_body.get('hostname')
        osuser = req_body.get('OperatingSystemUser')
        ospass = req_body.get('OperatingSystemPass')
        rootpass = req_body.get('RootPass')
        
    logging.info('Checking for the passed parameters.')
    logging.info('AccountName: '+accountname)
    logging.info('Container: '+container)
    logging.info('SASCred: '+sascred)
    logging.info('hostname: '+host)
    logging.info('OperatingSystemUser: '+osuser)
    logging.info('OperatingSystemPass: '+ospass)
    
    
# Update the next three lines with your
# server's information
##    _stdin, _stdout,_stderr = client.exec_command("touch abc")
##    print(_stdout.read().decode())
##    name = _stdout.read().decode()
##    client.close()
#    accounturl = "https://jassapbits.blob.core.windows.net"
    accounturl = "https://"+accountname+".blob.core.windows.net"
    logging.info('AccountURL: '+accounturl)
#    cred="FtLah1vqmHzp7kqjeF6dykvdEOLIMMD9ZQt9xrq5ggrw6izE9u3otr+LHqkTf2bTSixN2BXtArWU+AStxlCpPw=="
#    blob_name = "S4HANA_2021_ISS_v0001ms.yaml"
    filepath = "/tmp/"
#    filename = "S4HANA_2021_ISS_v0001ms.yaml"
# Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(accounturl,sascred)
            
#    def sap_operation(host,instancenumber, osuser, ospass, operation):
#        url = "http://"+host+":5"+instancenumber+"13?wsdl"
#        client = Client(url, username=osuser, password=ospass)
#        result = client.service.GetProcessList()
#        if operation == "start":
#            result = client.service.Start()
#        elif operation == "stop":
#            result = client.service.Stop()
#        elif operation == "stopservice":
#            result = client.service.StopService()
#        elif operation == "startservice":
#            result = client.service.StartService("TS3")    
#        return result
    
    logging.info('Downloading the file from remote.')
    sapkerupg.download_file_from_remote(host, osuser, ospass, "/usr/sap/sapservices", "/tmp/sapservices")
    
    sapkerupg.download_blob_to_file(any,blob_service_client, container, sapexefile)
    sapkerupg.download_blob_to_file(any,blob_service_client, container, sapcarfile)
    
    sapkerupg.upload_file_to_remote(host, osuser, ospass, "/tmp/"+sapexefile, "/tmp/"+sapexefile)
    sapkerupg.upload_file_to_remote(host, osuser, ospass, "/tmp/"+sapcarfile, "/tmp/"+sapcarfile)
    
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    for line in Lines:
        if osuser in line:
            if "ASCS" in line:
                ascssysnr = line.split("/")[4][-2:]
            else:
                diasysnr = line.split("/")[4][-2:]    
         
#            sap_operation(host, sysnr, osuser, ospass, "stop")
#            sap_operation(host, sysnr, osuser, ospass, "stopservice")
    sapkerupg.run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function StopWait 300 0")
    sapkerupg.run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function StopWait 300 0")
    sapkerupg.run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function StopService")
    sapkerupg.run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function StopService")
            
#    run_remote_command(host, osuser, ospass, "cd /usr/sap/TS3/SYS/exe/uc/linuxx86_64; /tmp/"+sapcarfile+" -xvf "+sapexefile)        
#    run_remote_command(host, osuser, ospass, "/usr/sap/TS3/SYS/exe/uc/linuxx86_64/sapcpe pf=/sapmnt/TS3/profile/TS3_D02_ts3vm")        
#    run_remote_command(host, osuser, ospass, "/usr/sap/TS3/SYS/exe/uc/linuxx86_64/sapcpe pf=/sapmnt/TS3/profile/TS3_ASCS01_ts3vm")
#    run_remote_command(host, osuser, ospass, "/usr/sap/TS3/SYS/exe/uc/linuxx86_64/saproot.sh TS3")
    
#    for line in Lines:
#        if osuser in line:
#            sysnr = line.split("/")[4][-2:]
#            sap_operation(host, sysnr, osuser, ospass, "startservice")
#            sap_operation(host, sysnr, osuser, ospass, "start")
    
    return func.HttpResponse(
        f" {sysnr} This HTTP triggered function executed successfully",
        status_code=200
    )
