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
        
    def download_file_from_remote(server, loginid, loginpass, remotefile, localpath):
        port = 22
        transport = paramiko.Transport((server, port))
        transport.connect(username = loginid, password = loginpass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(remotefile, localpath)
        sftp.close()
        transport.close()
        
    def run_remote_command(server, loginid, loginpass, command):
        try:
            remotecommandclient = paramiko.client.SSHClient()
            remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            remotecommandclient.connect(server, username=loginid, password=loginpass)
            stdin, stdout, stderr = remotecommandclient.exec_command(command)
            return str(stdout.read())
        finally:
            remotecommandclient.close()
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    for line in Lines:
        if osuser in line:
            if "ASCS" in line:
                sid=line.split("/")[3]
    
    #output = run_remote_command(host, osuser, ospass, "chmod 777 /tmp/"+sapcarfile+" /tmp/"+sapexefile+";/tmp/"+sapcarfile+" -xvf /tmp/"+sapexefile+" -R /sapmnt/"+sid+"/exe/uc/linuxx86_64")
    
    return func.HttpResponse(
        f"{output}",
        status_code=200    )
