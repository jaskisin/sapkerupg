import logging

import azure.functions as func

import paramiko

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

#    name = req.params.get('name')
#    if not name:
#        try:
#            req_body = req.get_json()
#        except ValueError:
#            pass
#        else:
#            name = req_body.get('name')
    command = "df"

# Update the next three lines with your
# server's information

    host = "10.0.0.7"
    username = "demouser"
    password = "Demo@pass123"

    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    _stdin, _stdout,_stderr = client.exec_command("df")
    print(_stdout.read().decode())
    name = _stdout.read().decode()
    client.close()

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
