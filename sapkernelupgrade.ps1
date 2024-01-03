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
$requesturibackupexe = "<Function URL for SapKerUpgBackupExe>"
$requesturiuploadexe = "<Function URL for SapKerUpgUploadExe>"
$requesturimain = "<Function URL for SapKerUpgMain>"
$requesturipoststeps = "<Function URL for SapKerUpgPostSteps>"
$requesturisapops = "<Function URL for SAPKerUpgSAPOps>"
"Fetching SAP Virtual Instances..."
$allvis = Get-AzWorkloadsSapVirtualInstance
"Getting SAS Credential..."
$SASCredential = (Get-AzStorageAccountKey -ResourceGroupName $BitsStorageAccountRGName -AccountName $BitsStorageAccountName | Select-Object -First 1).Value
ForEach ( $SAPSID in $SAPSIDs)
{
    # Variables
    "Getting VIS Details..."
    $vis = $allvis | Where-Object {$_.Name -eq $SAPSID}
    "Found VIS Admin User"
    $VISResourceGroup = $vis.ResourceGroupName
    "Found VIS Resource Group:  $VISResourceGroup"
    $VISName = $vis.Name
    "Found VIS Name:  $VISName"
    $VISManagedResourceGroupName = $vis.ManagedResourceGroupConfigurationName
    "Found VIS Managed Resource Group:  $VISManagedResourceGroupName"
    $VISKeyVault = (Get-AzKeyVault -ResourceGroupName $VISManagedResourceGroupName).VaultName
    "Found VIS Key Vault:  $VISKeyVault"
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

    if ($VISCS.VMDetail.Count -gt 1) {
        $VISDeploymentType = "HighAvailability"
    }
    elseif (($VISCS.VMDetail.VirtualMachineId | Select-Object -First 1) -eq ($VISAPPs.VMDetail.VirtualMachineId | Select-Object -First 1)) {
        $VISDeploymentType = "SingleServer"
    }
    else {
        $VISDeploymentType = "Distributed"
    }

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
    # Backup exe
    $requesturibackupexeinputobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser}
    $requesturibackupexeinputjson = $requesturibackupexeinputobj | ConvertTo-Json
    "Backing up the Current SAP Kernel to location /sapmnt/$SAPSID/exe/uc/linuxx86_64.tar"
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
    "Uploading new SAR files to the SAP host"
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
        "Stopping Application Server Instance on host $VISapphost"
        try {
            $responsesapopstopapp = Stop-AzWorkloadsSapApplicationInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISappname
            $StatusCode = $responsesapopstopapp.Status
            "Stopping of Application server completed successfully for $VISName with status $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
    
        # Stop app service
        $requesturisapopsinputstopsrvappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StopService";SysNr=$VISappsysnr;SysType="D"}
        $requesturisapopsinputstopsrvappjson = $requesturisapopsinputstopsrvappobj | ConvertTo-Json
        "Stopping Application Server Service on host $VISapphost"
        try {
            $responsesapopstopsrvapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopsrvappjson -Method 'POST' -UseBasicParsing
            $StatusCode = $responsesapopstopsrvapp.StatusCode
            "Stopping of Application server service completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
        
        if ($VISDeploymentType -ne "SingleServer") {
           # kill sidadm process
        $requesturisapopsinputstopforceobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="KillAll";SysNr=$VISappsysnr;SysType="D"}
        $requesturisapopsinputstopforcejson = $requesturisapopsinputstopforceobj | ConvertTo-Json
        "Killing remaining sidadm process on host $VISapphost"
            $responsesapopstopforce = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopforcejson -Method 'POST' -UseBasicParsing -ErrorAction SilentlyContinue
            $StatusCode = $responsesapopstopforce.StatusCode
            "Killing of sidadm process completed for $VISName with status code $StatusCode"
        }
    }

    "Stopping Message Server Instance on host $VISapphost"
    try {
        $responsesapopstopms = Stop-AzWorkloadsSapCentralInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISmsname
        $StatusCode = $responsesapopstopms.Status
        "Stopping of Message server completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    # Stop ms service
    $requesturisapopsinputstopsrvmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StopService";SysNr=$VISmssysnr;SysType="ASCS"}
    $requesturisapopsinputstopsrvmsjson = $requesturisapopsinputstopsrvmsobj | ConvertTo-Json
    "Stopping Message Server Service on host $VISapphost"
    try {
        $responsesapopstopsrvms = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopsrvmsjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responsesapopstopsrvms.StatusCode
        "Stopping of Message server service completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }
    

   # kill sidadm process
   $requesturisapopsinputstopforceobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="KillAll";SysNr=$VISmssysnr;SysType="ASCS"}
   $requesturisapopsinputstopforcejson = $requesturisapopsinputstopforceobj | ConvertTo-Json
   "Killing remaining sidadm process on host $VISapphost"
       $responsesapopstopforce = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstopforcejson -Method 'POST' -UseBasicParsing -ErrorAction SilentlyContinue
       $StatusCode = $responsesapopstopforce.StatusCode
       "Killing of sidadm process completed for $VISName with status code $StatusCode"

   # Main
   $requesturimaininputobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPExeFiles=$SAPExeFiles;SAPCarFile=$SAPCarFile}
   $requesturimaininputjson = $requesturimaininputobj | ConvertTo-Json
   "Performing Kernel Upgrade Main Task for $VISName"
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
        "Post Kernel Upgrade task on application Server on host $VISapphost"
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
    "Post Kernel Upgrade task on Message Server on host $VISmshost"
    try {
        $responsepostms = Invoke-WebRequest $requesturipoststeps -Body $requesturipostmsinputjson -Method 'POST' -UseBasicParsing
        $StatusCode = $responsepostms.StatusCode
        "Post Kernel Upgrade task on Message Server has completed successfully for $VISName with status code $StatusCode"
    }
    catch {
        throw $_.Exception.Response.StatusCode.value__
    }

    # start ms service
    $requesturisapopsinputstartsrvmsobj = @{IpAddress=$VISmsIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StartService";SysNr=$VISmssysnr;SysType="ASCS"}
    $requesturisapopsinputstartsrvmsjson = $requesturisapopsinputstartsrvmsobj | ConvertTo-Json
    "Starting Message Server Service on host $VISapphost"
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
    "Starting Message Server Instance on host $VISapphost"
    try {
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
        $requesturisapopsinputstartsrvappobj = @{IpAddress=$VISappIp;sshkey=$VISsshKey;SID=$VISName;AdminUserName=$VISDeploymentAdminUser;SAPOperation="StartService";SysNr=$VISappsysnr;SysType="D"}
        $requesturisapopsinputstartsrvappjson = $requesturisapopsinputstartsrvappobj | ConvertTo-Json
        "Starting Application Server Service on host $VISapphost"
        try {
            $responsesapopstartsrvapp = Invoke-WebRequest $requesturisapops -Body $requesturisapopsinputstartsrvappjson -Method 'POST' -UseBasicParsing
            $StatusCode = $responsesapopstartsrvapp.StatusCode
            "Starting of Application server service completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
        Start-Sleep -s 60
        "Starting Application Server Instance on host $VISapphost"
        try {
            $responsesapopstartapp = Start-AzWorkloadsSapApplicationInstance -ResourceGroupName $VISResourceGroup -SapVirtualInstanceName $VISName -Name $VISappname
            $StatusCode = $responsesapopstartapp.Status        
            "Starting of Application server completed successfully for $VISName with status code $StatusCode"
        }
        catch {
            throw $_.Exception.Response.StatusCode.value__
        }
    }
}
