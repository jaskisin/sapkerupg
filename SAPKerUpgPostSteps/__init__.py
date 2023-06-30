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
        ipaddress = req_body.get('IpAddress')
        host = req_body.get('hostname')
        sshkey = req_body.get('sshkey')
        sid = req_body.get('SID')
        sysnr = req_body.get('SysNr')
        typ = req_body.get('SysType')
        adminuser = req_body.get('AdminUserName')        

    logging.info('Checking for the passed parameters in request body.')
    logging.info('hostname: '+host)
    logging.info('SID: '+sid)
    logging.info('SysNr: '+sysnr)
    logging.info('SysType: '+typ)
    logging.info('IpAddress: '+ipaddress)

    # Creating the private key object
    logging.info('Creating the private key object.')
    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
        
    # Performing the sapcpe and saproot.sh command
    logging.info('Performing the sapcpe and saproot.sh command.')
    if typ == "ASCS":
        profile = "/usr/sap/"+sid+"/SYS/profile/"+sid+"_ASCS"+sysnr+"_"+host
    elif typ == "DIA":
        profile = "/usr/sap/"+sid+"/SYS/profile/"+sid+"_D"+sysnr+"_"+host
    remote_command_client = paramiko.client.SSHClient()
    remote_command_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_command_client.connect(ipaddress, username=adminuser, pkey=privatekey)
    logging.info("Command: sudo su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe pf="+profile+"\"")
    stdin, stdout, stderr = remote_command_client.exec_command("sudo su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe pf="+profile+"\"", get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    if returncode != 0:
        logging.error("Error in sapcpe command for "+typ+".")
        return func.HttpResponse(
            "Error in sapcpe command for "+typ+".",
            status_code=400
        )
    
    logging.info('Executing the saproot.sh command.')
    logging.info('Command: sudo /sapmnt/'+sid+'/exe/uc/linuxx86_64/saproot.sh '+sid)
    stdin, stdout, stderr = remote_command_client.exec_command("sudo /sapmnt/"+sid+"/exe/uc/linuxx86_64/saproot.sh "+sid, get_pty=True)
    returncode = stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resps = ''.join(outlines)
    for resp in resps.splitlines():
        logging.info(resp)
    if returncode != 0:
        logging.error("Error in executing saproot.sh")
        return func.HttpResponse(
            "Error in executing saproot.sh",
            status_code=400
        )
    remote_command_client.close()
    
    logging.info('SAP Kernel upgrade post steps completed successfully.')
    return func.HttpResponse(
        "SAP Kernel upgrade post steps completed successfully.",
        status_code=200
    )
