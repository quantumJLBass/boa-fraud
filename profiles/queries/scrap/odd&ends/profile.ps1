# Check if running as Administrator
If (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "This script needs to be run as Administrator. Please restart with elevated privileges." -ForegroundColor Red
    exit
}

# Initialize the output file
$outputFile = "E:\profile.md"
"## System Profile Report" | Out-File $outputFile

# System information using WMI and Get-WmiObject
"### System Information" | Out-File $outputFile -Append
(Get-WmiObject -Class Win32_OperatingSystem) | Select-Object Caption, OSArchitecture, Version, BuildNumber, TotalVisibleMemorySize | Out-File $outputFile -Append

# CPU information using WMI
"### CPU Information" | Out-File $outputFile -Append
Get-CimInstance -ClassName Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Out-File $outputFile -Append

# GPU information using WMI
"### GPU Information" | Out-File $outputFile -Append
Get-CimInstance -ClassName Win32_VideoController | Select-Object Name, AdapterRAM | Out-File $outputFile -Append

# Memory information using WMI
"### Memory Information" | Out-File $outputFile -Append
Get-CimInstance -ClassName Win32_PhysicalMemory | Select-Object Manufacturer, Capacity, Speed | Out-File $outputFile -Append

# Installed features using Get-WindowsFeature
"### Installed Windows Features" | Out-File $outputFile -Append
Get-WindowsFeature | Where-Object { $_.Installed -eq $True } | Select-Object DisplayName, Name | Out-File $outputFile -Append

# Installed programs using WMI
"### Installed Programs" | Out-File $outputFile -Append
Get-WmiObject -Query "SELECT * FROM Win32_Product" | Select-Object Name, Version | Out-File $outputFile -Append

# Check for Docker
"### Docker Version" | Out-File $outputFile -Append
docker --version | Out-File $outputFile -Append

# Check for Node.js
"### Node.js Version" | Out-File $outputFile -Append
node --version | Out-File $outputFile -Append

# Check for Python
"### Python Version" | Out-File $outputFile -Append
python --version | Out-File $outputFile -Append

# Check for .NET SDKs and runtimes
"### .NET SDKs and Runtimes" | Out-File $outputFile -Append
dotnet --list-sdks | Out-File $outputFile -Append
dotnet --list-runtimes | Out-File $outputFile -Append

# Check for Visual Studio
"### Visual Studio Installed Versions" | Out-File $outputFile -Append
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\SxS\VS7" | Select-Object Version | Out-File $outputFile -Append

# Check for CMake
"### CMake Version" | Out-File $outputFile -Append
cmake --version | Out-File $outputFile -Append

# Check for AutoHotKey
"### AutoHotKey Presence" | Out-File $outputFile -Append
if (Get-Command AutoHotKey -ErrorAction SilentlyContinue) {
    "AutoHotKey is installed." | Out-File $outputFile -Append
} else {
    "AutoHotKey is not installed." | Out-File $outputFile -Append
}

# Check for PyCharm
"### PyCharm Presence" | Out-File $outputFile -Append
if (Get-Item "C:\Program Files\JetBrains\PyCharm*" -ErrorAction SilentlyContinue) {
    "PyCharm is installed." | Out-File $outputFile -Append
} else {
    "PyCharm is not installed." | Out-File $outputFile -Append
}

# Check for Cursor
"### Cursor Presence" | Out-File $outputFile -Append
if (Get-Item "C:\Program Files\Cursor*" -ErrorAction SilentlyContinue) {
    "Cursor is installed." | Out-File $outputFile -Append
} else {
    "Cursor is not installed." | Out-File $outputFile -Append
}

# Check for Etcher
"### Etcher Presence" | Out-File $outputFile -Append
if (Get-Item "C:\Program Files\balenaEtcher*" -ErrorAction SilentlyContinue) {
    "Etcher is installed." | Out-File $outputFile -Append
} else {
    "Etcher is not installed." | Out-File $outputFile -Append
}

# List installed Chocolatey packages (if available)
"### Installed Chocolatey Packages" | Out-File $outputFile -Append
if (Get-Command choco -ErrorAction SilentlyContinue) {
    choco list --local-only | Out-File $outputFile -Append
} else {
    "Chocolatey is not installed." | Out-File $outputFile -Append
}

# List installed programs under Program Files
"### Installed Programs (Program Files)" | Out-File $outputFile -Append
Get-ChildItem "C:\Program Files\" | Select Name | Out-File $outputFile -Append
Get-ChildItem "C:\Program Files (x86)\" | Select Name | Out-File $outputFile -Append

# Finish
"Profile completed at $(Get-Date)" | Out-File $outputFile -Append

# Output message
Write-Host "Profile report has been generated at $outputFile" -ForegroundColor Green
