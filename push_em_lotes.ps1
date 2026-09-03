# push_em_lotes.ps1
# Envia os devocionais novos (textos, catalogo e audios) em lotes pequenos,
# para evitar o erro "RPC failed; HTTP 500" causado por push muito grande.
#
# Cada lote e um commit + push separado. Se der erro no meio, o script para
# e voce pode rodar de novo depois - os lotes ja enviados nao sao reenviados.

$batchSize = 25

Write-Host "=== Etapa 1: enviando o catalogo (devocionais.json) e os textos (.odt) ==="
git add devocionais.json
git add textos/
git commit -m "Atualiza catalogo com novos devocionais (textos)"
if ($LASTEXITCODE -eq 0) {
    git push
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO no push do catalogo/textos. Resolva isso antes de rodar o script de novo."
        exit 1
    }
} else {
    Write-Host "Nada novo para commitar no catalogo/textos (ja estava tudo enviado). Seguindo para os audios."
}

Write-Host ""
Write-Host "=== Etapa 2: enviando os audios em lotes de $batchSize ==="

$audioFiles = Get-ChildItem -Path "audio" -Filter "*.mp3" | Select-Object -ExpandProperty FullName
$total = $audioFiles.Count
$batchNum = 0

for ($i = 0; $i -lt $total; $i += $batchSize) {
    $batchNum++
    $endIndex = [Math]::Min($i + $batchSize - 1, $total - 1)
    $batch = $audioFiles[$i..$endIndex]

    Write-Host ""
    Write-Host "--- Lote $batchNum : arquivos $($i+1) a $($endIndex+1) de $total ---"

    foreach ($file in $batch) {
        git add -- "$file"
    }

    git commit -m "Adiciona audios - lote $batchNum"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Nada para commitar neste lote (provavelmente ja enviado). Pulando para o proximo."
        continue
    }

    git push
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERRO no push do lote $batchNum. PARANDO AQUI."
        Write-Host "Os lotes anteriores ja foram enviados com sucesso."
        Write-Host "Depois de resolver, rode o script de novo - ele vai continuar dos audios que faltam."
        exit 1
    }
}

Write-Host ""
Write-Host "=== Concluido! Todos os lotes de audio foram enviados. ==="
