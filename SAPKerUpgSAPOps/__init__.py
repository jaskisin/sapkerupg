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
        osuser = req_body.get('OperatingSystemUser')
        ospass = req_body.get('OperatingSystemPass')
        sapops = req_body.get('SAPOperation')
        
    logging.info('Checking for the passed parameters.')
    logging.info('hostname: '+host)
    logging.info('OperatingSystemUser: '+osuser)
    logging.info('OperatingSystemPass: '+ospass)

    def download_file_from_remote(server, loginid, loginpass, remotefile, localpath):
        port = 22
        transport = paramiko.Transport((server, port))
        transport.connect(username = loginid, password = loginpass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(remotefile, localpath)
        sftp.close()
        transport.close()
    
    def run_remote_command(server, loginid, loginpass, command):
        remotecommandclient = paramiko.client.SSHClient()
        remotecommandclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remotecommandclient.connect(server, username=loginid, password=loginpass)
        stdin, stdout, stderr = remotecommandclient.exec_command(command)
        remotecommandclient.close()
        return stdout.read().decode()
        
    download_file_from_remote(host, osuser, ospass, "/usr/sap/sapservices", "/tmp/sapservices")
    
    logging.info('Reading the file.')
    file1 = open('/tmp/sapservices', 'r')
    Lines = file1.readlines()
    
    for line in Lines:
        if osuser in line:
            if "ASCS" in line:
                ascssysnr = line.split("/")[4][-2:]
                sid=line.split("/")[3]
            else:
                diasysnr = line.split("/")[4][-2:]
                sid=line.split("/")[3]
    
    if sapops == "Stop":
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function Stop")
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function Stop")
    elif sapops == "Start":
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function Start")
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function Start")
    elif sapops == "StopService":
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function StopService")
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function StopService")
    elif sapops == "StartService":
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+ascssysnr+" -function StartService "+sid)
        run_remote_command(host, osuser, ospass, "sapcontrol -nr "+diasysnr+" -function StartService "+sid)
    elif sapops == "KillAll":
        run_remote_command(host, osuser, ospass, "killall -u "+osuser)
        
    return func.HttpResponse(
        f" {sid} This HTTP triggered function executed successfully.",
        status_code=200
    )
