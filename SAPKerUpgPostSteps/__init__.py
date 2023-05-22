import logging

import azure.functions as func

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
        sid = req_body.get('SID')

    transport = paramiko.Transport((host, 22))
    transport.connect(username = "root", password = rootpass)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get("/usr/sap/sapservices", "/tmp/sapservices")
    sftp.close()
    transport.close()
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    for line in Lines:
        if sid+"adm" in line:
            if "ASCS" in line:
                ascsprofile=line.split(" ")[2]
                sid=line.split("/")[3]
            else:
                diaprofile=line.split(" ")[2]
                sid=line.split("/")[3]
                
    remote_command_client = paramiko.client.SSHClient()
    remote_command_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_command_client.connect(host, username="root", password=rootpass)
    stdin, stdout, stderr = remote_command_client.exec_command("su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe "+ascsprofile+"\"", get_pty=True)
    stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resp = ''.join(outlines)
    logging.info('Output: %s', resp)
    stdin, stdout, stderr = remote_command_client.exec_command("su - "+sid.lower()+"adm -c \"/sapmnt/"+sid+"/exe/uc/linuxx86_64/sapcpe "+diaprofile+"\"", get_pty=True)
    stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resp = ''.join(outlines)
    logging.info('Output: %s', resp)
    stdin, stdout, stderr = remote_command_client.exec_command("/sapmnt/"+sid+"/exe/uc/linuxx86_64/saproot.sh "+sid, get_pty=True)
    stdout.channel.recv_exit_status()
    outlines = stdout.readlines()
    resp = ''.join(outlines)
    logging.info('Output: %s', resp)
    remote_command_client.close()
    return func.HttpResponse(
        "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
        status_code=200
    )
