# Repair Loop CMD Fix

## Zweck

Dieser Fix vermeidet PowerShell-Fehlwertungen von normalen Git-stderr-Ausgaben.

Alle kritischen Befehle laufen über `cmd.exe /c` mit getrennten Ausgabedateien.

## Start

Echten DeepSeek-Schlüssel nur als Sitzungsvariable setzen:

`$env:DEEPSEEK_API_KEY = "ECHTER_KEY"`

Dann:

`& "I:\KI_Legal_Project\Scripts\Run_AI_Coding_Agent_Repair_Loop.ps1"`
