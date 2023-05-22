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
        host = req_body.get('hostname')
        rootpass = req_body.get('RootPass')
        sapops = req_body.get('SAPOperation')
        sid = req_body.get('SID')
        
    logging.info('Checking for the passed parameters.')
    logging.info('hostname: '+host)
    logging.info('SAPOperation: '+sapops)

    # def download_file_from_remote(server, loginid, loginpass, remotefile, localpath):
    #     port = 22
    #     transport = paramiko.Transport((server, port))
    #     transport.connect(username = loginid, password = loginpass)
    #     sftp = paramiko.SFTPClient.from_transport(transport)
    #     sftp.get(remotefile, localpath)
    #     sftp.close()
    #     transport.close()
    
    def run_remote_command(server, loginid, loginpass, command):
        remotecommandclient = paramiko.client.SSHClient()
        remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remotecommandclient.connect(server, username=loginid, password=loginpass)
        stdin, stdout, stderr = remotecommandclient.exec_command(command)
        returncode = stdout.channel.recv_exit_status()
        outlines = stdout.readlines()
        resps = ''.join(outlines)
        for resp in resps.splitlines():
            logging.info(resp)
        remotecommandclient.close()
        # return stdout.read().decode()
        return returncode
        
    logging.info('Getting the sapservices file.')
    transport = paramiko.Transport((host, 22))
    transport.connect(username = 'root', password = rootpass)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get("/usr/sap/sapservices", "/tmp/sapservices")
    sftp.close()
    transport.close() 
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    # for line in Lines:
    #     if "ASCS" in line:
    #         sid=line.split("/")[3]
    logging.info('SID: '+sid)    
    for line in Lines:
        if sid.lower()+"adm" in line:
            if "ASCS" in line:
                ascssysnr = line.split("/")[4][-2:]
            else:
                diasysnr = line.split("/")[4][-2:]
    
    if sapops == "Stop":
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+diasysnr+" -function Stop\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" DIA instance.",
                status_code=400
            )
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+ascssysnr+" -function Stop\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" ASCS instance.",
                status_code=400
            )
    elif sapops == "Start":
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+ascssysnr+" -function Start\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in starting the "+sid+" ASCS instance.",
                status_code=400
            )
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+diasysnr+" -function Start\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in starting the "+sid+" DIA instance.",
                status_code=400
            )
    elif sapops == "StopService":
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+diasysnr+" -function StopService\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" DIA Service.",
                status_code=400
            )
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+ascssysnr+" -function StopService\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in stopping the "+sid+" ASCS Service.",
                status_code=400
            )
    elif sapops == "StartService":
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+ascssysnr+" -function StartService "+sid+"\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in Starting the "+sid+" ASCS Service.",
                status_code=400
            )
        rc = run_remote_command(host, 'root', rootpass, "su - "+sid.lower()+"adm -c \"sapcontrol -nr "+diasysnr+" -function StartService "+sid+"\"")
        if rc != 0:
            return func.HttpResponse(
                "Error in Starting the "+sid+" DIA Service.",
                status_code=400
            )
    elif sapops == "KillAll":
        rc = run_remote_command(host, 'root', rootpass, "killall -u "+sid.lower()+"adm")
        if rc != 0:
            return func.HttpResponse(
                "Error in killing prcesses with "+sid+"adm user.",
                status_code=400
            )
        
    return func.HttpResponse(
        f" {sapops} Operation has been executed successfully for {sid}.",
        status_code=200
    )
