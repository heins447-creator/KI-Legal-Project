# PaddleOCR Offline-Installation (vorbereitet fuer manuelle Ausfuehrung)
# Achtung: Erfordert Internet fuer ersten Download, danach offline-faehig
$ErrorActionPreference = "Stop"
$ProjektPython = "I:\KI_Legal_Project\Tools\Python312\python.exe"

Write-Host "PaddleOCR wird installiert ..."

# 1) PaddlePaddle CPU
& $ProjektPython -m pip install paddlepaddle==2.6.2 --no-deps -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html

# 2) PaddleOCR
& $ProjektPython -m pip install paddleocr==2.7.3

# 3) LayoutParser (optional, fuer Layout-Analyse)
& $ProjektPython -m pip install layoutparser

Write-Host "PaddleOCR Installation abgeschlossen."
Write-Host "Modelle werden beim ersten Start automatisch heruntergeladen."
Write-Host "Bitte stellen Sie sicher, dass die Lizenzbedingungen von PaddleOCR eingehalten werden."
