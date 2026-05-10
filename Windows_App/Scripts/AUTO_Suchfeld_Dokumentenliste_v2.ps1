$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = "I:\KI_Legal_Project"
$XamlPath = Join-Path $Root "Windows_App\App\MainWindow.xaml"
$CodePath = Join-Path $Root "Windows_App\App\MainWindow.xaml.cs"
$BuildScript = Join-Path $Root "Windows_App\Scripts\Build_App.ps1"
$StartScript = Join-Path $Root "Windows_App\Scripts\Start_App.ps1"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupDir = Join-Path $LogDir "BACKUP_SUCHFELD_V2_$Ts"
$Log = Join-Path $LogDir "AUTO_SUCHFELD_V2_$Ts.txt"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function L {
    param([string]$Text)
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Log -Append
}

function Restore-AppFiles {
    Copy-Item -LiteralPath (Join-Path $BackupDir "MainWindow.xaml") -Destination $XamlPath -Force
    Copy-Item -LiteralPath (Join-Path $BackupDir "MainWindow.xaml.cs") -Destination $CodePath -Force
}

function Build-Or-Throw {
    L "Build wird gestartet."
    $Out = & $BuildScript 2>&1
    $Exit = $LASTEXITCODE
    $Out | Tee-Object -FilePath $Log -Append

    if ($Exit -ne 0) {
        throw "Build fehlgeschlagen. ExitCode: $Exit"
    }

    L "Build erfolgreich."
}

try {
    L "AUTO Suchfeld Dokumentenliste v2 gestartet."

    $Dirty = (git -C $Root status --short | Out-String).Trim()
    if ($Dirty) {
        throw "Arbeitsstand ist nicht sauber: $Dirty"
    }

    Copy-Item -LiteralPath $XamlPath -Destination (Join-Path $BackupDir "MainWindow.xaml") -Force
    Copy-Item -LiteralPath $CodePath -Destination (Join-Path $BackupDir "MainWindow.xaml.cs") -Force

    $Xaml = [System.IO.File]::ReadAllText($XamlPath)
    $Code = [System.IO.File]::ReadAllText($CodePath)

    if ($Xaml -notmatch 'x:Name="DokumentenFilterTextBox"') {
        L "XAML Suchfeld wird ergänzt."

        $HeaderMarker = '<TextBlock Text="Arbeitsbereich"'
        $HeaderIndex = $Xaml.IndexOf($HeaderMarker, [System.StringComparison]::Ordinal)
        if ($HeaderIndex -lt 0) {
            throw "Arbeitsbereich-Überschrift nicht gefunden."
        }

        $RowStart = $Xaml.LastIndexOf('<Grid.RowDefinitions>', $HeaderIndex, [System.StringComparison]::Ordinal)
        if ($RowStart -lt 0) {
            throw "RowDefinitions vor Arbeitsbereich nicht gefunden."
        }

        $RowEndMarker = '</Grid.RowDefinitions>'
        $RowEnd = $Xaml.IndexOf($RowEndMarker, $RowStart, [System.StringComparison]::Ordinal)
        if ($RowEnd -lt 0) {
            throw "Ende der RowDefinitions nicht gefunden."
        }

        $RowEnd = $RowEnd + $RowEndMarker.Length

        $NewRows = @(
            '                    <Grid.RowDefinitions>'
            '                        <RowDefinition Height="Auto"/>'
            '                        <RowDefinition Height="Auto"/>'
            '                        <RowDefinition Height="*"/>'
            '                    </Grid.RowDefinitions>'
        ) -join [Environment]::NewLine

        $Xaml = $Xaml.Substring(0, $RowStart) + $NewRows + $Xaml.Substring($RowEnd)

        $HeaderEnd = $Xaml.IndexOf('/>', $HeaderIndex, [System.StringComparison]::Ordinal)
        if ($HeaderEnd -lt 0) {
            throw "Ende der Arbeitsbereich-Überschrift nicht gefunden."
        }

        $HeaderEnd = $HeaderEnd + 2

        $FilterBox = @(
            ''
            '                    <TextBox x:Name="DokumentenFilterTextBox"'
            '                             Grid.Row="1"'
            '                             Height="28"'
            '                             Margin="0,0,0,8"'
            '                             VerticalContentAlignment="Center"'
            '                             TextChanged="DokumentenFilterTextBox_TextChanged"'
            '                             ToolTip="Nach Datei oder Pfad filtern"/>'
        ) -join [Environment]::NewLine

        $Xaml = $Xaml.Substring(0, $HeaderEnd) + $FilterBox + $Xaml.Substring($HeaderEnd)

        $OldList = '<ListView x:Name="DokumentenListe" Grid.Row="1" SelectionChanged="DokumentenListe_SelectionChanged">'
        $NewList = '<ListView x:Name="DokumentenListe" Grid.Row="2" SelectionChanged="DokumentenListe_SelectionChanged">'

        if (-not $Xaml.Contains($OldList)) {
            throw "DokumentenListe mit Grid.Row 1 nicht gefunden."
        }

        $Xaml = $Xaml.Replace($OldList, $NewList)
    }
    else {
        L "XAML Suchfeld ist bereits vorhanden."
    }

    if ($Code -notmatch 'using System\.Collections\.Generic;') {
        $Code = $Code.Replace("using System;", "using System;`r`nusing System.Collections.Generic;")
    }

    if ($Code -notmatch '_alleDokumente') {
        L "C# Dokumenten-Zwischenspeicher wird ergänzt."

        $OldFields = @(
            '        private readonly string _root;'
            '        private readonly string _logFile;'
        ) -join [Environment]::NewLine

        $NewFields = @(
            '        private readonly string _root;'
            '        private readonly string _logFile;'
            '        private List<DocumentRow> _alleDokumente = new();'
        ) -join [Environment]::NewLine

        if (-not $Code.Contains($OldFields)) {
            throw "Feldposition für _alleDokumente nicht gefunden."
        }

        $Code = $Code.Replace($OldFields, $NewFields)
    }

    if ($Code -notmatch 'DokumentenFilterTextBox_TextChanged') {
        L "C# Filterlogik wird ergänzt."

        $OldItems = '            DokumentenListe.ItemsSource = files;'
        $NewItems = @(
            '            _alleDokumente = files;'
            '            ApplyDocumentFilter();'
        ) -join [Environment]::NewLine

        if (-not $Code.Contains($OldItems)) {
            throw "ItemsSource-Stelle nicht gefunden."
        }

        $Code = $Code.Replace($OldItems, $NewItems)

        $Anchor = '        private void DokumentenListe_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)'
        if (-not $Code.Contains($Anchor)) {
            throw "Einfügeposition vor DokumentenListe_SelectionChanged nicht gefunden."
        }

        $Methods = @(
            '        private void DokumentenFilterTextBox_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)'
            '        {'
            '            ApplyDocumentFilter();'
            '        }'
            ''
            '        private void ApplyDocumentFilter()'
            '        {'
            '            string filter = DokumentenFilterTextBox.Text.Trim();'
            ''
            '            if (string.IsNullOrWhiteSpace(filter))'
            '            {'
            '                DokumentenListe.ItemsSource = _alleDokumente;'
            '                StatusTextBlock.Text = "Dokumente geladen: " + _alleDokumente.Count;'
            '                return;'
            '            }'
            ''
            '            string[] teile = filter.Split('
            "                ' ',"
            '                StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);'
            ''
            '            var gefiltert = _alleDokumente'
            '                .Where(row => teile.All(teil =>'
            '                    row.Name.Contains(teil, StringComparison.OrdinalIgnoreCase) ||'
            '                    row.Extension.Contains(teil, StringComparison.OrdinalIgnoreCase) ||'
            '                    row.FullName.Contains(teil, StringComparison.OrdinalIgnoreCase)))'
            '                .ToList();'
            ''
            '            DokumentenListe.ItemsSource = gefiltert;'
            '            StatusTextBlock.Text = "Filter: " + gefiltert.Count + " von " + _alleDokumente.Count;'
            '        }'
            ''
            $Anchor
        ) -join [Environment]::NewLine

        $Code = $Code.Replace($Anchor, $Methods)
    }
    else {
        L "C# Filterlogik ist bereits vorhanden."
    }

    [System.IO.File]::WriteAllText($XamlPath, $Xaml, $Utf8NoBom)
    [System.IO.File]::WriteAllText($CodePath, $Code, $Utf8NoBom)

    try {
        Build-Or-Throw
    }
    catch {
        L "Buildfehler. Rollback wird ausgeführt."
        Restore-AppFiles
        Build-Or-Throw
        throw "Änderungen wurden wegen Buildfehler zurückgerollt."
    }

    $Status = (git -C $Root status --short | Out-String).Trim()
    L "Git-Status nach Build:"
    L $Status

    if ($Status) {
        git -C $Root add Windows_App/App/MainWindow.xaml Windows_App/App/MainWindow.xaml.cs 2>&1 | Tee-Object -FilePath $Log -Append
        git -C $Root commit -m "Suchfeld für Dokumentenliste ergänzt" 2>&1 | Tee-Object -FilePath $Log -Append
        L "Commit erstellt."
    }
    else {
        L "Keine Änderungen zu sichern."
    }

    L "App wird gestartet."
    & $StartScript

    L "AUTO Suchfeld Dokumentenliste v2 erfolgreich abgeschlossen."
    Write-Host "FERTIG"
    Write-Host $Log
}
catch {
    L ("FEHLER: " + $_.Exception.Message)
    Write-Host "FEHLER"
    Write-Host $Log
    throw
}
