import logging

import azure.functions as func

import os,stat

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
        sapops = req_body.get('SAPOperation')
        sid = req_body.get('SID')
        sysnr = req_body.get('SysNr')
        adminuser = req_body.get('AdminUserName')        
        

    logging.info('Checking for the passed parameters.')
    logging.info('IpAddress: '+ipaddress)
    logging.info('SAPOperation: '+sapops)
    logging.info('SID: '+sid)

    parasshkey = sshkey.replace("\r\n","\n")
    privatekeyfile = StringIO(parasshkey)
    privatekey = paramiko.RSAKey.from_private_key(privatekeyfile)
        
    # Function to run remote commands.
    def run_remote_command(server, loginid, sshpass, command):
        remotecommandclient = paramiko.client.SSHClient()
        remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remotecommandclient.connect(server, username=loginid, pkey=sshpass)
        stdin, stdout, stderr = remotecommandclient.exec_command(command)
        returncode = stdout.channel.recv_exit_status()
        outlines = stdout.readlines()
        resps = ''.join(outlines)
        for resp in resps.splitlines():
            logging.info(resp)
        remotecommandclient.close()
        return returncode
        
    # Get the ASCS and DIA system numbers.
    # logging.info('Getting the sapservices file.')
    # transport = paramiko.Transport((host, 22))
    # transport.connect(username = 'azureuser', pkey=privatekey)
    # sftp = paramiko.SFTPClient.from_transport(transport)
    # sftp.get("/usr/sap/sapservices", "/tmp/sapservices")
    # sftp.close()
    # transport.close() 
    
    # logging.info('Reading the file.')
    # file1 = open('/tmp/sapservices', 'r')
    # Lines = file1.readlines()
    
    # logging.info(Lines)
    
    # logging.info('Getting the ASCS and DIA system numbers.')
    # for line in Lines:
    #     if sid.lower()+"adm" in line:
    #         if "ASCS" in line:
    #             ascssysnr = line.split("/")[4][-2:]
    #         else:
    #             diasysnr = line.split("/")[4][-2:]
    
    logging.info('System Number: '+sysnr)
    
    # Perform the SAP operation.
    if sapops == "Stop":
        logging.info('Stopping the DIA instances.')
        logging.info('Command: '+'su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function Stop"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function Stop\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" DIA instance.",
                status_code=400
            )
    elif sapops == "Start":
        logging.info('Starting the ASCS instances.')
        logging.info('Command: '+'su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function Start"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function Start\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in starting the "+sid+" ASCS instance.",
                status_code=400
            )

    elif sapops == "StopService":
        logging.info('Stopping the DIA Service.')
        logging.info('Command: '+'su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StopService"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StopService\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" DIA Service.",
                status_code=400
            )
    elif sapops == "StartService":
        logging.info('Starting the ASCS Service.')
        logging.info('Command: '+'su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StartService '+sid+'"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StartService "+sid+"\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in Starting the "+sid+" ASCS Service.",
                status_code=400
            )
            
    elif sapops == "KillAll":
        logging.info('Killing the processes with '+sid+'adm user.')
        logging.info('Command: '+'killall -u '+sid.lower()+'adm')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo killall -u "+sid.lower()+"adm")
        if rc != 0:
            return func.HttpResponse(
                "Error in killing prcesses with "+sid+"adm user.",
                status_code=400
            )
        
    return func.HttpResponse(
        f" {sapops} Operation has been executed successfully for {sid}.",
        status_code=200
    )
