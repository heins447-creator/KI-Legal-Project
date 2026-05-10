# Aider Conf and Loop Finalfix

## Zweck

Aider las `.aider.conf.yml` wegen UTF-8-BOM als `ï»¿model`.

Außerdem wurde `yes:` statt `yes-always:` beanstandet.

Dieser Fix schreibt `.aider.conf.yml` BOM-frei und paßt den Repair-Loop so an, daß Aider-Fehler nicht mehr als Erfolg gewertet werden.

## Start

`$env:DEEPSEEK_API_KEY = "ECHTER_KEY"`

`& "I:\KI_Legal_Project\Scripts\Run_AI_Coding_Agent_Repair_Loop.ps1"`
