import logging

import azure.functions as func

import os,stat

import paramiko

from io import StringIO

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Reading the request body
    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        host = req_body.get('hostname')
        sshkey = req_body.get('sshkey')
        sid = req_body.get('SID')

    logging.info('Checking for the passed parameters in request body.')
    logging.info('hostname: '+host)
    logging.info('SID: '+sid)

    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
        
    # Getting the sapservices file
    logging.info('Getting the sapservices file.')
    transport = paramiko.Transport((host, 22))
    transport.connect(username="azureuser", pkey=privatekey)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get("/usr/sap/sapservices", "/tmp/sapservices")
    sftp.close()
    transport.close()
    
    # Reading the sapservices file
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    # Getting the ASCS and DIA profiles
    for line in Lines:
        if sid.lower()+"adm" in line:
            if "ASCS" in line:
                ascsprofile=line.split(" ")[2]
                logging.info('ASCS profile: '+ascsprofile)
            else:
                diaprofile=line.split(" ")[2]
                logging.info('DIA profile: '+diaprofile)
    
    # Performing the sapcpe and saproot.sh command                
    remote_command_client = paramiko.client.SSHClient()
    remote_command_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_command_client.connect(host, username="azureuser", pkey=privatekey)
    logging.info('Executing the sapcpe command for ASCS profile.')
    logging.info('Command: su - '+sid.lower()+'adm -c "/sapmnt/'+sid+'/exe/uc/linuxx86_64/sapcpe '+ascsprofile+'"')
    stdin, stdout, stderr = remote_command_client.exec_command("sudo su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe "+ascsprofile+"\"", get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    if returncode != 0:
        return func.HttpResponse(
            "Error in sapcpe command for ASCS.",
            status_code=400
        )
    
    logging.info('Executing the sapcpe command for DIA profile.')
    logging.info('Command: su - '+sid.lower()+'adm -c "/sapmnt/'+sid+'/exe/uc/linuxx86_64/sapcpe '+diaprofile+'"')
    stdin, stdout, stderr = remote_command_client.exec_command("sudo su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe "+diaprofile+"\"", get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    if returncode != 0:
        return func.HttpResponse(
            "Error in sapcpe command for DIA.",
            status_code=400
        )
    
    logging.info('Executing the saproot.sh command.')
    logging.info('Command: /sapmnt/'+sid+'/exe/uc/linuxx86_64/saproot.sh '+sid)
    stdin, stdout, stderr = remote_command_client.exec_command("sudo /sapmnt/"+sid+"/exe/uc/linuxx86_64/saproot.sh "+sid, get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    if returncode != 0:
        return func.HttpResponse(
            "Error in executing saproot.sh",
            status_code=400
        )
    remote_command_client.close()
    
    return func.HttpResponse(
        "SAP Kernel upgrade post steps completed successfully.",
        status_code=200
    )
