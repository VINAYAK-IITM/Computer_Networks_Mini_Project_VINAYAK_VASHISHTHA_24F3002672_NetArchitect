$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$entryPoint = Join-Path $projectRoot "netarchitect\__main__.py"
$verificationRoot = Join-Path $projectRoot "output\verification"

Push-Location $projectRoot
try {
    Write-Host "== Unit tests ==" -ForegroundColor Cyan
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Unit test suite failed with exit code $LASTEXITCODE." }

    Write-Host "== Preset CLI and exports ==" -ForegroundColor Cyan
    python -u $entryPoint list-profiles
    if ($LASTEXITCODE -ne 0) { throw "Profile listing failed." }

    foreach ($scenarioId in @("campus", "metro", "global")) {
        $destination = Join-Path $verificationRoot $scenarioId
        python -u $entryPoint generate $scenarioId --out $destination
        if ($LASTEXITCODE -ne 0) { throw "Generation failed for '$scenarioId'." }
    }

    Write-Host "== Custom profile ==" -ForegroundColor Cyan
    $customOutput = Join-Path $verificationRoot "custom"
    python -u $entryPoint generate-custom (Join-Path $projectRoot "examples\custom-profile.json") --out $customOutput
    if ($LASTEXITCODE -ne 0) { throw "Custom profile generation failed." }

    Write-Host "== ACL packet-flow decisions ==" -ForegroundColor Cyan
    $denyText = python -u $entryPoint flow campus --acl GUEST-TO-MANAGEMENT --source 10.10.6.10 --destination 10.10.7.65 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "ACL deny flow command failed." }
    $denyResult = $denyText | ConvertFrom-Json
    if ($denyResult.decision -ne "deny") { throw "Expected guest-to-management traffic to be denied." }

    $permitText = python -u $entryPoint flow campus --acl GUEST-TO-MANAGEMENT --source 10.10.6.10 --destination 8.8.8.8 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "ACL permit flow command failed." }
    $permitResult = $permitText | ConvertFrom-Json
    if ($permitResult.decision -ne "permit") { throw "Expected this ACL to permit the public-DNS flow." }
    Write-Host "Guest-to-management: deny (expected); guest-to-public-DNS: permit by this ACL (expected)."

    Write-Host "== Export and documentation files ==" -ForegroundColor Cyan
    $requiredFiles = @("report.md", "address_plan.csv", "network_plan.json", "core_switch.cfg", "edge_router.cfg")
    foreach ($scenarioId in @("campus", "metro", "global", "custom")) {
        foreach ($fileName in $requiredFiles) {
            $filePath = Join-Path (Join-Path $verificationRoot $scenarioId) $fileName
            if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
                throw "Missing expected export: $filePath"
            }
        }
    }

    $auditLog = Join-Path $projectRoot "docs\ai_audit_log.md"
    if (-not (Test-Path -LiteralPath $auditLog -PathType Leaf)) {
        throw "AI audit log is missing: $auditLog"
    }

    Write-Host "SOFTWARE VERIFICATION PASSED. Exports are under output\verification." -ForegroundColor Green
}
finally {
    Pop-Location
}
