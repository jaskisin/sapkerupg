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
        rootpass = req_body.get('RootPass')
        sid = req_body.get('SID')
        
    logging.info('Checking for the passed parameters in request body.')
    logging.info('AccountName: '+accountname)
    logging.info('Container: '+container)
    logging.info('SASCred: '+sascred)
    logging.info('hostname: '+host)
    
    # def download_file_from_remote(server, loginid, loginpass, remotefile, localpath):
    #     port = 22
    #     transport = paramiko.Transport((server, port))
    #     transport.connect(username = loginid, password = loginpass)
    #     sftp = paramiko.SFTPClient.from_transport(transport)
    #     sftp.get(remotefile, localpath)
    #     sftp.close()
    #     transport.close()    
    
    # def download_blob_to_file(self, accounturl, sascred, container_name, storagefilename, filepath):
    #     blob_service_client = BlobServiceClient(accounturl,sascred)
    #     blob_client = blob_service_client.get_blob_client(container=container_name, blob=storagefilename)
    #     with open(file=os.path.join(filepath, storagefilename), mode="wb") as sample_blob:
    #         download_stream = blob_client.download_blob()
    #         sample_blob.write(download_stream.readall())
        
    # def upload_file_to_remote(server, loginid, loginpass, remotepath, localpath):
    #     client = paramiko.client.SSHClient()
    #     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     client.connect(server, username=loginid, password=loginpass)
    #     sftp = client.open_sftp()
    #     sftp.put(localpath, remotepath)
    #     sftp.close()
    #     client.close()
        
    # def run_remote_command(server, loginid, loginpass, command):
    #     remotecommandclient = paramiko.client.SSHClient()
    #     remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     remotecommandclient.connect(server, username=loginid, password=loginpass)
    #     stdin, stdout, stderr = remotecommandclient.exec_command(command)
    #     remotecommandclient.close()
    #     return stdout.read().decode()
        
    accounturl = "https://"+accountname+".blob.core.windows.net"
    logging.info('AccountURL: '+accounturl)
    
    logging.info('Downloading file '+sapexefile+' from blob storage.')
    blob_service_client = BlobServiceClient(accounturl,sascred)
    blob_client = blob_service_client.get_blob_client(container=container, blob=sapexefile)
    with open(file=os.path.join("/tmp/", sapexefile), mode="wb") as sample_blob:
        download_stream = blob_client.download_blob()
        sample_blob.write(download_stream.readall())
    logging.info('Downloading file '+sapcarfile+' from blob storage.')
    blob_client = blob_service_client.get_blob_client(container=container, blob=sapcarfile)
    with open(file=os.path.join("/tmp/", sapcarfile), mode="wb") as sample_blob:
        download_stream = blob_client.download_blob()
        sample_blob.write(download_stream.readall())
        
    
    
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username='root', password=rootpass)
    sftp = client.open_sftp()
    logging.info('Uploading file '+sapexefile+' to remote host.')
    sftp.put("/tmp/"+sapexefile, "/tmp/"+sapexefile)
    logging.info('Uploading file '+sapcarfile+' to remote host.')
    sftp.put("/tmp/"+sapcarfile, "/tmp/"+sapcarfile)
    sftp.close()
    client.close()
    
    
    # logging.info('Getting the sapservices file.')
    # transport = paramiko.Transport((host, 22))
    # transport.connect(username = 'root', password = rootpass)
    # sftp = paramiko.SFTPClient.from_transport(transport)
    # sftp.get("/usr/sap/sapservices", "/tmp/sapservices")
    # sftp.close()
    # transport.close() 
    
    # logging.info('Reading the file.')
    # file1 = open('/tmp/sapservices', 'r')
    # Lines = file1.readlines()
    # for line in Lines:
    #     if "ASCS" in line:
    #         sid=line.split("/")[3]
    # logging.info('SID: '+sid)

    logging.info('Backing up the kernel.')
    remotecommandclient = paramiko.client.SSHClient()
    remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remotecommandclient.connect(host, username='root', password=rootpass)
    stdin, stdout, stderr = remotecommandclient.exec_command("tar -cvf /tmp/sapkernelbackup.tar.gz /sapmnt/"+sid+"/exe/uc/linuxx86_64", get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    remotecommandclient.close()
    if returncode != 0:
        return func.HttpResponse(
            "Error in backing up the kernel.",
            status_code=400
        )

    return func.HttpResponse(
        "Success",
        status_code=200
    )
