# Regenerates the Pac-Man contribution graphs and pushes them if they changed.
# shortcut: runs on this PC instead of GitHub Actions (account Actions locked), upgrade back to the workflow once Actions works.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$themes = @{ 'assets/pacman.svg' = 'github'; 'assets/pacman-dark.svg' = 'github-dark' }
foreach ($out in $themes.Keys) {
    npx -y pacman-contribution-graph@5.5.2 --game pacman --username achmf --platform github --gameTheme $themes[$out] --output $out
    # The generator sometimes writes an empty game (rate limit); keep the old file in that case.
    if ((Select-String -Path $out -Pattern '<frames>0<' -Quiet)) {
        Write-Warning "$out came out empty, restoring previous version"
        git checkout -- $out
    }
    Start-Sleep -Seconds 30
}

git add assets/pacman.svg assets/pacman-dark.svg
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "chore: update pac-man graph"
    git push origin main
} else {
    Write-Output 'No change.'
}
