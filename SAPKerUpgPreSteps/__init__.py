import logging

import azure.functions as func

import os

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobLeaseClient, BlobPrefix, ContentSettings

import paramiko

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

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
    
    def download_file_from_remote(server, loginid, loginpass, remotefile, localpath):
        port = 22
        transport = paramiko.Transport((server, port))
        transport.connect(username = loginid, password = loginpass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(remotefile, localpath)
        sftp.close()
        transport.close()    
    
    def download_blob_to_file(self, accounturl, sascred, container_name, storagefilename, filepath):
        blob_service_client = BlobServiceClient(accounturl,sascred)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=storagefilename)
        with open(file=os.path.join(filepath, storagefilename), mode="wb") as sample_blob:
            download_stream = blob_client.download_blob()
            sample_blob.write(download_stream.readall())
        
    def upload_file_to_remote(server, loginid, loginpass, remotepath, localpath):
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, username=loginid, password=loginpass)
        sftp = client.open_sftp()
        sftp.put(localpath, remotepath)
        sftp.close()
        client.close()
        
    def run_remote_command(server, loginid, loginpass, command):
        remotecommandclient = paramiko.client.SSHClient()
        remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remotecommandclient.connect(server, username=loginid, password=loginpass)
        stdin, stdout, stderr = remotecommandclient.exec_command(command)
        remotecommandclient.close()
        return stdout.read().decode()
        
    accounturl = "https://"+accountname+".blob.core.windows.net"
    logging.info('AccountURL: '+accounturl)
    
    download_blob_to_file(any,accounturl, sascred, container, sapexefile, "/tmp")
    download_blob_to_file(any,accounturl, sascred, container, sapcarfile, "/tmp")
    
    upload_file_to_remote(host, osuser, ospass, "/tmp/"+sapexefile, "/tmp/"+sapexefile)
    upload_file_to_remote(host, osuser, ospass, "/tmp/"+sapcarfile, "/tmp/"+sapcarfile)
    
    download_file_from_remote(host, osuser, ospass, "/usr/sap/sapservices", "/tmp/sapservices")
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    for line in Lines:
        if osuser in line:
            if "ASCS" in line:
                sid=line.split("/")[3]
    
    output = run_remote_command(host, osuser, ospass, "tar -czvf /tmp/sapkernelbackup.tar.gz /sapmnt/"+sid+"/exe/uc/linuxx86_64")

    return func.HttpResponse(
         f" {output}",
         status_code=200
    )
