Param
(
    [Parameter (Mandatory= $true)]
    [String] $MSIApplicationID,

    [Parameter (Mandatory= $true)]
    [String] $BitsStorageAccountRGName,

    [Parameter (Mandatory= $true)]
    [String] $BitsStorageAccountName,

    [Parameter (Mandatory= $true)]
    [String] $BitsStorageContainerName,

    [Parameter (Mandatory= $true)]
    [String] $SAPExeFiles,

    # [String] $SAPExeDBFile,

    # [String] $SAPERSFile,

    [Parameter (Mandatory= $true)]
    [String] $SAPCarFile,

    [Parameter (Mandatory= $true)]
    [String] $SAPSIDs
)

try
{ 
    "Logging in to Azure..." 
    Connect-AzAccount -Identity -AccountId $MSIApplicationID
} 
catch { 
    Write-Error -Message $_.Exception 
    throw $_.Exception 
} 

$ErrorActionPreference = "Stop"
"Getting Request URIs..."
$requesturibackupexe = "https://sapkerupg.azurewebsites.net/api/SapKerUpgBackupExe?code=XSNIttwbaNYpqfp5Y5hOlPIsL_zeCTyFn6btW-4yH4U6AzFuyxq7wQ=="
$requesturiuploadexe = "https://sapkerupg.azurewebsites.net/api/SapKerUpgUploadExe?code=QghiVcaRV4t2CuqM2typpi0NMObFd-DsdelHY6W5A8FBAzFutOYtGA=="
$requesturimain = "https://sapkerupg.azurewebsites.net/api/SAPKerUpgMain?code=20CY-q4Cd0ZTBvXuU6xEG7BRJvYlJVM9Cl34ZJ-ptwYJAzFurkyLCw=="
$requesturipoststeps = "https://sapkerupg.azurewebsites.net/api/SAPKerUpgPostSteps?code=1SByLrgYXnZw7jmGa3QgyVtHOCT0IRKZtBmxLRGJAP7fAzFu62K9_g=="
$requesturisapops = "https://sapkerupg.azurewebsites.net/api/SAPKerUpgSAPOps?code=T1BsiSKxzGPWDGLd592gce4MYreV4yiR6P08OWXnmPEmAzFulPoV5A=="
# $requesturibackupexe = "https://sapkerupg1.azurewebsites.net/api/SapKerUpgBackupExe?code=OteL6pchPhS4vS0Fd8KCRP8g6o_OeULKOWwT-Lu3cYTcAzFu89D2iw=="
# $requesturiuploadexe = "https://sapkerupg1.azurewebsites.net/api/SapKerUpgUploadExe?code=rKRnwLBB6IXIBd-5bJcT7zetWt36eOTx-183yTx7I504AzFuCKf7qw=="
# $requesturimain = "https://sapkerupg1.azurewebsites.net/api/SAPKerUpgMain?code=AI5EUXP-UQMCY3fAKNl-KlzjcFx5zd7UHvY-4YlYOabDAzFu7qXPag=="
# $requesturipoststeps = "https://sapkerupg1.azurewebsites.net/api/SAPKerUpgPostSteps?code=ZirHyAaWHcrrD4Bej0c80pAIQulwrTEXCml_2SwH6MchAzFuO1etoQ=="
# $requesturisapops = "https://sapkerupg1.azurewebsites.net/api/SAPKerUpgSAPOps?code=uDYxZvTXQxTUrT4EhjhtdZjRYprNF4sAOw4lpndHEZgtAzFun_LbPw=="
"Fetching SAP Virtual Instances..."
$allvis = Get-AzWorkloadsSapVirtualInstance
"Getting SAS Credential..."
$SASCredential = (Get-AzStorageAccountKey -ResourceGroupName $BitsStorageAccountRGName -AccountName $BitsStorageAccountName | Select-Object -First 1).Value
ForEach ( $SAPSID in $SAPSIDs)
{
    # Variables
    "Getting VIS Details..."
    $vis = $allvis | Where-Object {$_.Name -eq $SAPSID}
    $VISDeploymentType = ($vis.Configuration | ConvertFrom-Json).infrastructureConfiguration.deploymentType
    "Found VIS Deployment Type:  $VISDeploymentType"
    if ($VISDeploymentType -eq "SingleServer")
    {
        $VISDeploymentAdminUser = ($vis.Configuration | ConvertFrom-Json).infrastructureConfiguration.virtualMachineConfiguration.osProfile.adminUsername
    }
    else
    {
        $VISDeploymentAdminUser = ($vis.Configuration | ConvertFrom-Json).infrastructureConfiguration.centralServer.virtualMachineConfiguration.osProfile.adminUsername
    }
    "Found VIS Admin User"
    $VISResourceGroup = $vis.ResourceGroupName
    "Found VIS Resource Group:  $VISResourceGroup"
    $VISName = $vis.Name
    "Found VIS Name:  $VISName"
    $VISManagedResourceGroupName = $vis.ManagedResourceGroupConfigurationName
    "Found VIS Managed Resource Group:  $VISManagedResourceGroupName"
    # $VISManagedStorageAccount = (Get-AzStorageAccount -ResourceGroupName $VISManagedResourceGroupName).StorageAccountName
    $VISKeyVault = (Get-AzKeyVault -ResourceGroupName $VISManagedResourceGroupName).VaultName
    "Found VIS Key Vault:  $VISKeyVault"
    "Allowing application to access VIS Key Vault..."
    $AppObjID = (Get-AzADServicePrincipal -ApplicationId $MSIApplicationID).Id
    $null = Set-AzKeyVaultAccessPolicy -VaultName $VISKeyVault -ObjectId $AppObjID -PermissionsToSecrets Get,Set,Delete
    "Getting VIS SSH Key..."
    $VISsshKey = Get-AzKeyVaultSecret -VaultName $VISKeyVault -Name "$VISNAME-sid-sshkey" -AsPlainText
    "Getting VIS Message Server Details..."
    $VISCS = Get-AzWorkloadsSapCentralInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName
    $VISmsname = $VISCS.Name
    $VISmsIp = $VISCS.MessageServerPropertyIPAddress
    "Found VIS Message Server IP:  $VISmsIp"
    $VISmssysnr = $VISCS.InstanceNo
    "Found VIS Message Server System Number:  $VISmssysnr"
    $VISmshost = $VISCS.MessageServerPropertyHostname
    "Found VIS Message Server Hostname:  $VISmshost"
    "Getting VIS Application Server Details..."
    $VISAPPs = Get-AzWorkloadsSapApplicationInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName

    # Backup exe
    $requesturibackupexeinputobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser}
    $requesturibackupexeinputjson = $requesturibackupexeinputobj | ConvertTo-Json
    "Backing up the Current SAP Kernel"
    try {
        $responseuribackupexe = Invoke-WebRequest $requesturibackupexe -Body $requesturibackupexeinputjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responseuribackupexe.StatusCode
        "Backup of Kernel Completed Successfully on VIS $VISName with Status Code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    # Upload exe
    $requesturiuploadexeinputobj = @{AccountName=$BitsStorageAccountName;Container=$BitsStorageContainerName;SASCred=$SASCredential;SAPExeFiles=$SAPExeFiles;SAPCarFile=$SAPCarFile;IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser}
    $requesturiuploadexeinputjson = $requesturiuploadexeinputobj | ConvertTo-Json
    "Uploading new SAR files to the host"
    try {
        $responseuploadexe = Invoke-WebRequest $requesturiuploadexe -Body $requesturiuploadexeinputjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responseuploadexe.StatusCode
        "Upload of SAR files Completed Successfully on VIS $VISName with Status Code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }
    
    ForEach ( $VISAPP in $VISAPPs )
    {
        $VISappIp = $VISAPP.IPAddress
        $VISappsysnr = $VISAPP.InstanceNo
        $VISapphost = $VISAPP.Hostname
        $VISappname = $VISAPP.Name
        # Stop app
        # $requesturisapopsinputstopappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="Stop";SysNr=$VISappsysnr}
        # $requesturisapopsinputstopappjson = $requesturisapopsinputstopappobj | ConvertTo-Json
        "Stopping Application Server Instance"
        try {
            # $responsesapopstopapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopappjson -Method 'POST' -UseBasicParsing
            $responsesapopstopapp = Stop-AzWorkloadsSapApplicationInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISappname
            $StatusCode = $responsesapopstopapp.Status
            "Stopping of Application server completed successfully for $VISName with status $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
    
        # Stop app service
        $requesturisapopsinputstopsrvappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StopService";SysNr=$VISappsysnr}
        $requesturisapopsinputstopsrvappjson = $requesturisapopsinputstopsrvappobj | ConvertTo-Json
        "Stopping Application Server Service"
        try {
            $responsesapopstopsrvapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopsrvappjson -Method 'POST' -UseBasicParsing
            $StatusCode = $responsesapopstopsrvapp.StatusCode
            "Stopping of Application server service completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }

           # kill sidadm process
        $requesturisapopsinputstopforceobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="KillAll";SysNr=$VISappsysnr}
        $requesturisapopsinputstopforcejson = $requesturisapopsinputstopforceobj | ConvertTo-Json
        "Killing remaining sidadm process"
        # try {
            $responsesapopstopforce = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopforcejson -Method 'POST' -UseBasicParsing -ErrorAction SilentlyContinue
            $StatusCode = $responsesapopstopforce.StatusCode
            "Killing of sidadm process completed for $VISName with status code $StatusCode"
        # }
        # catch {
        #     throw $_.Exception.Response.StatusCode.value__
        # } 
    }


    # Stop ms
    # $requesturisapopsinputstopmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="Stop";SysNr=$VISmssysnr}
    # $requesturisapopsinputstopmsjson = $requesturisapopsinputstopmsobj | ConvertTo-Json
    "Stopping Message Server Instance"
    try {
        # $responsesapopstopms = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopmsjson -Method 'POST' -UseBasicParsing
        $responsesapopstopms = Stop-AzWorkloadsSapCentralInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISmsname
        $StatusCode = $responsesapopstopms.Status
        "Stopping of Message server completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    # Stop ms service
    $requesturisapopsinputstopsrvmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StopService";SysNr=$VISmssysnr}
    $requesturisapopsinputstopsrvmsjson = $requesturisapopsinputstopsrvmsobj | ConvertTo-Json
    "Stopping Message Server Service"
    try {
        $responsesapopstopsrvms = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopsrvmsjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responsesapopstopsrvms.StatusCode
        "Stopping of Message server service completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }
    

   # kill sidadm process
   $requesturisapopsinputstopforceobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="KillAll";SysNr=$VISmssysnr}
   $requesturisapopsinputstopforcejson = $requesturisapopsinputstopforceobj | ConvertTo-Json
   "Killing remaining sidadm process"
#    try {
       $responsesapopstopforce = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopforcejson -Method 'POST' -UseBasicParsing -ErrorAction SilentlyContinue
       $StatusCode = $responsesapopstopforce.StatusCode
       "Killing of sidadm process completed for $VISName with status code $StatusCode"
#    }
#    catch {
#          throw $_.Exception.Response.StatusCode.value__
#    } 
   
   # Main
   $requesturimaininputobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPExeFiles=$SAPExeFiles;SAPCarFile=$SAPCarFile}
   $requesturimaininputjson = $requesturimaininputobj | ConvertTo-Json
   "Performing Kernel Upgrade Main Task"
   try {
       $responsemain = Invoke-WebRequest $requesturimain -Body $requesturimaininputjson -Method 'POST' -UseBasicParsing
       $StatusCode = $responsemain.StatusCode
       "Kernel Upgrde Main Task completed successfully for $VISName with status code $StatusCode"
   }
   catch {
         throw $_.Exception.Response.StatusCode.value__
   }
   
   ForEach ( $VISAPP in $VISAPPs )
   {
       $VISappIp = $VISAPP.IPAddress
       $VISappsysnr = $VISAPP.InstanceNo
       $VISapphost = $VISAPP.Hostname
       $VISappname = $VISAPP.Name
        # Post Kernel Upgrade app
        $requesturipostappinputobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;hostname=$VISapphost;SysNr=$VISappsysnr;SysType="DIA"}
        $requesturipostappinputjson = $requesturipostappinputobj | ConvertTo-Json
        "Post Kernel Upgrade task on application Server"
        try {
            $responsepostapp = Invoke-WebRequest $requesturipoststeps -Body $requesturipostappinputjson -Method 'POST' -UseBasicParsing
            $StatusCode = $responsepostapp.StatusCode
            "Post Kernel Upgrade task on Application Server has completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
   }

    # Post Kernel Upgrade ms
    $requesturipostmsinputobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;hostname=$VISmshost;SysNr=$VISmssysnr;SysType="ASCS"}
    $requesturipostmsinputjson = $requesturipostmsinputobj | ConvertTo-Json
    "Post Kernel Upgrade task on Message Server"
    try {
        $responsepostms = Invoke-WebRequest $requesturipoststeps -Body $requesturipostmsinputjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responsepostms.StatusCode
        "Post Kernel Upgrade task on Message Server has completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    # start ms service
    $requesturisapopsinputstartsrvmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StartService";SysNr=$VISmssysnr}
    $requesturisapopsinputstartsrvmsjson = $requesturisapopsinputstartsrvmsobj | ConvertTo-Json
    "Starting Message Server Service"
    try {
        $responsesapopstartsrvms = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstartsrvmsjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responsesapopstartsrvms.StatusCode
        "Starting of Message server service completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    Start-Sleep -s 60
    # start ms
    # $requesturisapopsinputstartmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="Start";SysNr=$VISmssysnr}
    # $requesturisapopsinputstartmsjson = $requesturisapopsinputstartmsobj | ConvertTo-Json
    "Starting Message Server Instance"
    try {
        # $responsesapopstartms = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstartmsjson -Method 'POST' -UseBasicParsing
        # $StatusCode = $responsesapopstartms.StatusCode
        $responsesapopstartms = Start-AzWorkloadsSapCentralInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISmsname
        $StatusCode = $responsesapopstartms.Status
        "Starting of Message server completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    ForEach ( $VISAPP in $VISAPPs )
    {
        # Start app
        $VISappIp = $VISAPP.IPAddress
        $VISappsysnr = $VISAPP.InstanceNo
        $VISapphost = $VISAPP.Hostname
        $VISappname = $VISAPP.Name
        # Start app service
        $requesturisapopsinputstartsrvappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StartService";SysNr=$VISappsysnr}
        $requesturisapopsinputstartsrvappjson = $requesturisapopsinputstartsrvappobj | ConvertTo-Json
        "Starting Application Server Service"
        try {
            $responsesapopstartsrvapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstartsrvappjson -Method 'POST' -UseBasicParsing
            $StatusCode = $responsesapopstartsrvapp.StatusCode
            "Starting of Application server service completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
        Start-Sleep -s 60
        # $requesturisapopsinputstartappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="Start";SysNr=$VISappsysnr}
        # $requesturisapopsinputstartappjson = $requesturisapopsinputstartappobj | ConvertTo-Json
        "Starting Application Server Instance"
        try {
            # $responsesapopstartapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstartappjson -Method 'POST' -UseBasicParsing
            # $StatusCode = $responsesapopstartapp.StatusCode
            $responsesapopstartapp = Start-AzWorkloadsSapApplicationInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISappname
            $StatusCode = $responsesapopstartapp.Status        
            "Starting of Application server completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
    }
}