import logging

import azure.functions as func

import os,stat

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobLeaseClient, BlobPrefix, ContentSettings

import paramiko

from io import StringIO

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Check for the passed parameters in request body.
    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        accountname = req_body.get('AccountName')
        container = req_body.get('Container')
        sascred = req_body.get('SASCred')
        sapexefiles = req_body.get('SAPExeFiles')
        sapcarfile = req_body.get('SAPCarFile')
        ipaddress = req_body.get('IpAddress')
        adminuser = req_body.get('AdminUserName')
        sshkey = req_body.get('sshkey')
        sid = req_body.get('SID')
        
    logging.info('Checking for the passed parameters in request body.')
    logging.info('AccountName: '+accountname)
    logging.info('Container: '+container)
    logging.info('SASCred: '+sascred)
    logging.info('IpAddress: '+ipaddress)
          
    accounturl = "https://"+accountname+".blob.core.windows.net"
    logging.info('AccountURL: '+accounturl)
    
    # Download the kernel files from blob storage.
    for sapexefile in sapexefiles.split(','):
        logging.info('Downloading file '+sapexefile+' from blob storage.')
        blob_service_client = BlobServiceClient(accounturl,sascred)
        blob_client = blob_service_client.get_blob_client(container=container, blob=sapexefile)
        with open(file=os.path.join("/tmp/"+sapexefile), mode="wb") as sample_blob:
            download_stream = blob_client.download_blob()
            sample_blob.write(download_stream.readall())
            
    logging.info('Downloading file '+sapcarfile+' from blob storage.')
    blob_client = blob_service_client.get_blob_client(container=container, blob=sapcarfile)
    with open(file=os.path.join("/tmp/"+sapcarfile), mode="wb") as sample_blob:
        download_stream = blob_client.download_blob()
        sample_blob.write(download_stream.readall())
    
    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
    # Upload the kernel files to remote host.
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ipaddress, username=adminuser, pkey=privatekey)
    sftp = client.open_sftp()
    for sapexefile in sapexefiles.split(','):
        logging.info('Uploading file '+sapexefile+' to remote host.')
        sftp.put("/tmp/"+sapexefile, "/sapmnt/"+sid+"/"+sapexefile)
    logging.info('Uploading file '+sapcarfile+' to remote host.')
    sftp.put("/tmp/"+sapcarfile, "/sapmnt/"+sid+"/"+sapcarfile)
    sftp.close()
    client.close()

    return func.HttpResponse(
        "Pre-Steps completed successfully.",
        status_code=200
    )