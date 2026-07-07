$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AndroidSdk = $env:ANDROID_HOME
if ([string]::IsNullOrWhiteSpace($AndroidSdk)) {
  $AndroidSdk = $env:ANDROID_SDK_ROOT
}
if ([string]::IsNullOrWhiteSpace($AndroidSdk)) {
  $AndroidSdk = 'D:\env\android-sdk'
}
if (-not (Test-Path -LiteralPath $AndroidSdk)) {
  throw "Android SDK not found. Set ANDROID_HOME or ANDROID_SDK_ROOT first."
}

$BuildToolsDir = Join-Path $AndroidSdk 'build-tools'
$BuildTools = Get-ChildItem -LiteralPath $BuildToolsDir -Directory |
  Sort-Object { [version]$_.Name } -Descending |
  Select-Object -First 1 -ExpandProperty FullName
if ([string]::IsNullOrWhiteSpace($BuildTools)) {
  throw "No Android build-tools found under $BuildToolsDir"
}

$AndroidJar = Join-Path $AndroidSdk 'platforms\android-35\android.jar'
if (-not (Test-Path -LiteralPath $AndroidJar)) {
  $AndroidJar = Get-ChildItem -LiteralPath (Join-Path $AndroidSdk 'platforms') -Directory |
    Where-Object { $_.Name -match '^android-\d+$' } |
    Sort-Object { [int]($_.Name -replace '^android-', '') } -Descending |
    Select-Object -First 1 |
    ForEach-Object { Join-Path $_.FullName 'android.jar' }
}
if ([string]::IsNullOrWhiteSpace($AndroidJar)) {
  throw "No android.jar found under Android SDK platforms."
}

$Aapt2 = Join-Path $BuildTools 'aapt2.exe'
$D8 = Join-Path $BuildTools 'd8.bat'
$ZipAlign = Join-Path $BuildTools 'zipalign.exe'
$ApkSigner = Join-Path $BuildTools 'apksigner.bat'
$KeyTool = Join-Path (Split-Path -Parent (Get-Command java).Source) 'keytool.exe'

foreach ($path in @($Aapt2, $D8, $ZipAlign, $ApkSigner, $AndroidJar, $KeyTool)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required build tool: $path"
  }
}

$BuildDir = Join-Path $ProjectRoot 'build'
$DistDir = Join-Path $ProjectRoot 'dist'
$GenDir = Join-Path $BuildDir 'gen'
$ClassDir = Join-Path $BuildDir 'classes'
$DexDir = Join-Path $BuildDir 'dex'
$CompiledRes = Join-Path $BuildDir 'compiled-res.zip'
$UnsignedApk = Join-Path $BuildDir 'cmake-docs-unsigned.apk'
$DexedApk = Join-Path $BuildDir 'cmake-docs-dex.apk'
$NormalizedApk = Join-Path $BuildDir 'cmake-docs-normalized.apk'
$AlignedApk = Join-Path $BuildDir 'cmake-docs-aligned.apk'
$SignedApk = Join-Path $DistDir 'cmake-docs-mobile.apk'
$Keystore = Join-Path $ProjectRoot 'debug.keystore'

Remove-Item -LiteralPath $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $GenDir, $ClassDir, $DexDir, $DistDir | Out-Null

& $Aapt2 compile --dir (Join-Path $ProjectRoot 'res') -o $CompiledRes
if ($LASTEXITCODE -ne 0) { throw "aapt2 compile failed" }

& $Aapt2 link `
  -o $UnsignedApk `
  -I $AndroidJar `
  --manifest (Join-Path $ProjectRoot 'AndroidManifest.xml') `
  --java $GenDir `
  --min-sdk-version 23 `
  --target-sdk-version 35 `
  --version-code 9 `
  --version-name '1.8' `
  $CompiledRes
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed" }

$JavaSources = @()
$JavaSources += Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'src') -Recurse -Filter *.java | ForEach-Object { $_.FullName }
$JavaSources += Get-ChildItem -LiteralPath $GenDir -Recurse -Filter *.java | ForEach-Object { $_.FullName }

& javac -encoding UTF-8 -source 8 -target 8 -classpath $AndroidJar -d $ClassDir $JavaSources
if ($LASTEXITCODE -ne 0) { throw "javac failed" }

$ClassFiles = Get-ChildItem -LiteralPath $ClassDir -Recurse -Filter *.class | ForEach-Object { $_.FullName }
& $D8 --min-api 23 --output $DexDir $ClassFiles
if ($LASTEXITCODE -ne 0) { throw "d8 failed" }

Copy-Item -LiteralPath $UnsignedApk -Destination $DexedApk -Force
Push-Location $DexDir
try {
  & jar uf $DexedApk classes.dex
  if ($LASTEXITCODE -ne 0) { throw "jar update failed" }
} finally {
  Pop-Location
}

& python (Join-Path $ProjectRoot 'tools\package_apk_assets.py') $DexedApk (Join-Path $ProjectRoot 'assets') $NormalizedApk
if ($LASTEXITCODE -ne 0) { throw "APK asset packaging failed" }

& $ZipAlign -f 4 $NormalizedApk $AlignedApk
if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

if (-not (Test-Path -LiteralPath $Keystore)) {
  & $KeyTool -genkeypair -v `
    -keystore $Keystore `
    -storepass android `
    -keypass android `
    -alias cmake-docs `
    -keyalg RSA `
    -keysize 2048 `
    -validity 10000 `
    -dname 'CN=CMake Docs,O=Local,C=CN'
  if ($LASTEXITCODE -ne 0) { throw "keytool failed" }
}

& $ApkSigner sign `
  --ks $Keystore `
  --ks-key-alias cmake-docs `
  --ks-pass pass:android `
  --key-pass pass:android `
  --out $SignedApk `
  $AlignedApk
if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

& $ApkSigner verify --verbose $SignedApk
if ($LASTEXITCODE -ne 0) { throw "apksigner verify failed" }

$IdSigPath = "$SignedApk.idsig"
if (Test-Path -LiteralPath $IdSigPath) {
  Remove-Item -LiteralPath $IdSigPath -Force -ErrorAction SilentlyContinue
}

Get-Item -LiteralPath $SignedApk | Select-Object FullName, Length
