import logging

import time

import azure.functions as func

import paramiko

import os,stat

from io import StringIO

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Check for the passed parameters in request body.
    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        sapexefiles = req_body.get('SAPExeFiles')
        sapcarfile = req_body.get('SAPCarFile')
        ipaddress = req_body.get('IpAddress')
        sshkey = req_body.get('sshkey')
        sid = req_body.get('SID')
        adminuser = req_body.get('AdminUserName')        
    
    logging.info('Checking for the passed parameters in request body.')
    logging.info('hostname: '+ipaddress)
    logging.info('SID: '+sid)
    logging.info('SAPExeFiles: '+sapexefiles)
    logging.info('SAPCarFile: '+sapcarfile)

    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
    
    # Extract the kernel.
    remote_command_client = paramiko.client.SSHClient()
    remote_command_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_command_client.connect(ipaddress, username=adminuser, pkey=privatekey)
    logging.info('Giving full permission to the files.')
    command = ""
    for sapexefile in sapexefiles.split(','):
        command += " /sapmnt/"+sid+"/"+sapexefile
    logging.info("Command: chmod 777"+command)
    stdin, stdout, stderr = remote_command_client.exec_command("sudo chmod 777 /sapmnt/"+sid+"/"+sapcarfile+command, get_pty=True)
    logging.info('Extracting the kernel.')
    for sapexefile in sapexefiles.split(','):
        logging.info("Command: /tmp/"+sapcarfile+" -xvf /tmp/"+sapexefile+" -R /sapmnt/"+sid+"/exe/uc/linuxx86_64")
        stdin, stdout, stderr = remote_command_client.exec_command("sudo su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/"+sapcarfile+" -xvf /sapmnt/"+sid+"/"+sapexefile+" -R /sapmnt/"+sid+"/exe/uc/linuxx86_64\"", get_pty=True)
        returncode = stdout.channel.recv_exit_status()
        outlines = stdout.readlines()
        resps = ''.join(outlines)
        for resp in resps.splitlines():
            logging.info(resp)
        if returncode != 0:
            return func.HttpResponse(
                "Error in extracing "+sapexefile+" the kernel.",
                status_code=400
            )
        time.sleep(1)
        stdin = None
        stdout = None
        stderr = None
        returncode = None
        outlines = None
        resps = None    
    remote_command_client.close()
       
    return func.HttpResponse(
        "Kernel extracted successfully.",
        status_code=200    )
