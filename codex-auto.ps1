param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CodexArgs
)

& python (Join-Path $PSScriptRoot "codex-auto.py") @CodexArgs
exit $LASTEXITCODE
