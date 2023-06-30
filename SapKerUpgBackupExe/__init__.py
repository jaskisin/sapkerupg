import logging

import azure.functions as func

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
        ipaddress = req_body.get('IpAddress')
        sshkey = req_body.get('sshkey')
        sid = req_body.get('SID')
        adminuser = req_body.get('AdminUserName')        
        
    logging.info('Checking for the passed parameters in request body.')
    logging.info('IpAddress: '+ipaddress)
    logging.info('SID: '+sid)
    
    # Convert the sshkey to private key.
    logging.info('Convert the sshkey to private key..')
    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
        
    # Backup the kernel.
    logging.info('Backing up the kernel..')
    remotecommandclient = paramiko.client.SSHClient()
    remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remotecommandclient.connect(ipaddress, username=adminuser, pkey=privatekey)
    logging.info("Command: sudo cp -rp /sapmnt/"+sid+"/exe/uc/linuxx86_64 /sapmnt/"+sid+"/exe/uc/linuxx86_64_bkp")
    stdin, stdout, stderr = remotecommandclient.exec_command("sudo su - root -c \"cp -rp /sapmnt/"+sid+"/exe/uc/linuxx86_64 /sapmnt/"+sid+"/exe/uc/linuxx86_64_bkp\"", get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    remotecommandclient.close()
    if returncode != 0:
        logging.error("Error in backing up the kernel.")
        return func.HttpResponse(
            "Error in backing up the kernel.",
            status_code=400
        )
        
    logging.info('Backup of current Exe has been finished successfully.')
    return func.HttpResponse(
        "Backup of current Exe has been finished successfully.",
        status_code=200
    )