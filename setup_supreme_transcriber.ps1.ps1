<#
.SYNOPSIS
  Script para configurar e rodar o projeto SupremeTranscriber no Windows,
  usando venv e pip, no diretório D:\SupremeTranscriber.
#>

# Impede que o script continue em caso de erro
$ErrorActionPreference = "Stop"

# Define o diretório do projeto
$projectDir = "D:\SupremeTranscriber"

Write-Host "=== Verificando se Python está instalado e disponível no PATH ==="
try {
    $pythonVersion = & python --version
} catch {
    Write-Error "Python não encontrado no PATH.
Instale o Python 3.9+ em https://www.python.org/downloads/ e marque 'Add Python to PATH' na instalação."
    exit 1
}

Write-Host "Encontrado: $pythonVersion"

Write-Host "`n=== Criando (ou confirmando) a pasta do projeto: $projectDir ==="
if (!(Test-Path $projectDir)) {
    New-Item -ItemType Directory -Path $projectDir | Out-Null
}
Set-Location $projectDir

Write-Host "`n=== Criando (ou recriando) ambiente virtual (venv) ==="
if (Test-Path ".\venv") {
    Write-Host "A pasta 'venv' já existe. Iremos recriar para garantir um setup limpo."
    Remove-Item -Recurse -Force ".\venv"
}
python -m venv .\venv

Write-Host "`n=== Ativando o venv para este script ==="
. "$projectDir\venv\Scripts\activate.ps1"

Write-Host "`n=== Atualizando pip ==="
pip install --upgrade pip

Write-Host "`n=== Instalando bibliotecas necessárias (Flask, PyAudio, Pyperclip, Vosk) ==="
pip install flask pyaudio pyperclip vosk

Write-Host "`n=== Estrutura atual do projeto ==="
Write-Host (ls)

Write-Host "`n=== Executando app.py (se existir) ==="
if (Test-Path ".\app.py") {
    Write-Host "Encontramos 'app.py'. Iremos executá-lo agora..."
    Write-Host "`n(Para encerrar o servidor Flask, pressione CTRL + C)"
    python .\app.py
} else {
    Write-Host "Nenhum 'app.py' encontrado em $projectDir. 
Coloque seu projeto aqui e rode novamente ou execute manualmente."
}

Write-Host "`n=== Fim do script. ==="
Write-Host "Para reativar o ambiente futuramente, abra o PowerShell e rode:"
Write-Host "    . $projectDir\venv\Scripts\activate.ps1"
