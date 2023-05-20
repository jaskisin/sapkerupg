
import os

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobLeaseClient, BlobPrefix, ContentSettings

import paramiko

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