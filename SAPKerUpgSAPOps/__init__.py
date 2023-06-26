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
    logging.info('SysNr: '+sysnr)

    # Create the private key object.
    logging.info('Creating the private key object.')
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
            
    # Perform the SAP operation.
    if sapops == "Stop":
        logging.info('Stopping the '+sysnr+'instance.')
        logging.info('Command: '+'sudo su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StopWait 300 0"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StopWait 300 0\"")
        if rc != 0:
            logging.info('Error in stopping the '+sysnr+' instance.')
            return func.HttpResponse(
                "Error in stopping the "+sysnr+" instance.",
                status_code=400
            )
    elif sapops == "Start":
        logging.info('Starting the '+sysnr+' instance.')
        logging.info('Command: '+'sudo su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StartWait 300 0"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StartWait 300 0\"")
        if rc != 0:
            logging.error('Error in starting the '+sysnr+' instance.')
            return func.HttpResponse(
                "Error in starting the "+sysnr+" instance.",
                status_code=400
            )

    elif sapops == "StopService":
        logging.info('Stopping the '+sysnr+' instance.')
        logging.info('Command: '+'sudo su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StopService"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StopService\"")
        if rc != 0:
            logging.error('Error in stopping the '+sysnr+' instance.')
            return func.HttpResponse(
                "Error in stopping the "+sysnr+" Service.",
                status_code=400
            )
    elif sapops == "StartService":
        logging.info('Starting Service for '+sysnr+' instance.')
        logging.info('Command: '+'sudo su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function StartService '+sid+'"')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function StartService "+sid+"\"")
        if rc != 0:
            logging.error('Error in starting service for '+sysnr+' instance.')
            return func.HttpResponse(
                "Error in Starting service for "+sysnr+" Service.",
                status_code=400
            )
        logging.info('Waiting for the service to Start.')
        logging.info('Command: '+'sudo su - '+sid.lower()+'adm -c "sapcontrol -nr '+sysnr+' -function WaitforServiceStarted 300 0')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo su - "+sid.lower()+"adm -c \"sapcontrol -nr "+sysnr+" -function WaitforServiceStarted 300 0")
        if rc != 0:
            logging.error('Error in starting service for '+sysnr+' instance.')
            return func.HttpResponse(
                "Error in Starting service for "+sysnr+" Service.",
                status_code=400
            )            
            
    elif sapops == "KillAll":
        logging.info('Killing the processes with '+sid+'adm user.')
        logging.info('Command: '+'sudo killall -u '+sid.lower()+'adm')
        rc = run_remote_command(ipaddress, adminuser, privatekey, "sudo killall -u "+sid.lower()+"adm")
        if rc != 0:
            logging.error('Error in killing prcesses with '+sid+'adm user.')
            return func.HttpResponse(
                "Error in killing prcesses with "+sid+"adm user.",
                status_code=400
            )
    
    logging.info(sapops+' Operation has been executed successfully for '+sid+'.')        
    return func.HttpResponse(
        f" {sapops} Operation has been executed successfully for {sid}.",
        status_code=200
    )
