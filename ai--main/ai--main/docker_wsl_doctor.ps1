param()

$ErrorActionPreference = "SilentlyContinue"

function Emit-Pair {
    param(
        [string]$Name,
        [string]$Value
    )

    if ($null -eq $Value -or $Value -eq "") {
        $Value = "Unknown"
    }

    $Value = $Value -replace "`r|`n", " "
    Write-Output ("{0}={1}" -f $Name, $Value)
}

function Get-FeatureState {
    param([string]$Name)

    $feature = Get-CimInstance Win32_OptionalFeature -Filter ("Name='{0}'" -f $Name)
    if ($null -eq $feature) {
        return "Missing"
    }

    if ($feature.InstallState -eq 1) {
        return "Enabled"
    }

    return "Disabled"
}

function Get-ServiceSnapshot {
    param([string]$Name)

    $service = Get-CimInstance Win32_Service -Filter ("Name='{0}'" -f $Name)
    if ($null -eq $service) {
        return @{ State = "Missing"; StartMode = "Unknown" }
    }

    return @{
        State = [string]$service.State
        StartMode = [string]$service.StartMode
    }
}

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$wslCmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
$wslCommandState = if ($wslCmd) { "Present" } else { "Missing" }
$wslStatus = "Unavailable"
if ($wslCmd) {
    & wsl.exe --status *> $null
    if ($LASTEXITCODE -eq 0) {
        $wslStatus = "Ready"
    } else {
        $wslStatus = "Error"
    }
}

$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$virtualizationFirmware = if ($cpu -and $cpu.VirtualizationFirmwareEnabled -eq $true) { "Enabled" } elseif ($cpu -and $cpu.VirtualizationFirmwareEnabled -eq $false) { "Disabled" } else { "Unknown" }
$slat = if ($cpu -and $cpu.SecondLevelAddressTranslationExtensions -eq $true) { "Enabled" } elseif ($cpu -and $cpu.SecondLevelAddressTranslationExtensions -eq $false) { "Disabled" } else { "Unknown" }

$localAppDataDrive = [System.IO.Path]::GetPathRoot($env:LOCALAPPDATA).TrimEnd('\')
$disk = if ($localAppDataDrive) { Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='{0}'" -f $localAppDataDrive) } else { $null }
$fileSystem = if ($disk) { [string]$disk.FileSystem } else { "Unknown" }

$vds = Get-ServiceSnapshot -Name "vds"
$dockerService = Get-ServiceSnapshot -Name "com.docker.service"

$dockerDesktopExe = ""
if (Test-Path "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe") {
    $dockerDesktopExe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
} elseif (Test-Path "$env:LocalAppData\Programs\Docker\Docker\Docker Desktop.exe") {
    $dockerDesktopExe = "$env:LocalAppData\Programs\Docker\Docker\Docker Desktop.exe"
}

$dockerInfoOk = "Missing"
$dockerContext = "Unknown"
$dockerCmd = Get-Command docker.exe -ErrorAction SilentlyContinue
if ($dockerCmd) {
    & docker.exe context show *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerContext = ((& docker.exe context show) 2>$null | Select-Object -First 1)
    }

    & docker.exe info *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerInfoOk = "Ready"
    } else {
        $dockerInfoOk = "Error"
    }
}

Emit-Pair "IS_ADMIN" ($(if ($isAdmin) { "Yes" } else { "No" }))
Emit-Pair "WSL_COMMAND" $wslCommandState
Emit-Pair "WSL_STATUS" $wslStatus
Emit-Pair "WSL_FEATURE" (Get-FeatureState -Name "Microsoft-Windows-Subsystem-Linux")
Emit-Pair "VMP_FEATURE" (Get-FeatureState -Name "VirtualMachinePlatform")
Emit-Pair "HYPERV_FEATURE" (Get-FeatureState -Name "Microsoft-Hyper-V-All")
Emit-Pair "VIRTUALIZATION_FIRMWARE" $virtualizationFirmware
Emit-Pair "SLAT" $slat
Emit-Pair "LOCALAPPDATA_DRIVE" $localAppDataDrive
Emit-Pair "LOCALAPPDATA_FS" $fileSystem
Emit-Pair "VDS_SERVICE_STATE" $vds.State
Emit-Pair "VDS_SERVICE_MODE" $vds.StartMode
Emit-Pair "DOCKER_SERVICE_STATE" $dockerService.State
Emit-Pair "DOCKER_SERVICE_MODE" $dockerService.StartMode
Emit-Pair "DOCKER_DESKTOP_EXE" $dockerDesktopExe
Emit-Pair "DOCKER_INFO_OK" $dockerInfoOk
Emit-Pair "DOCKER_CONTEXT" $dockerContext
