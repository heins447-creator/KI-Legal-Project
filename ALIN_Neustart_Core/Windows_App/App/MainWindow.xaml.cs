using System;
using System.IO;
using System.Text.Json;
using Microsoft.UI.Xaml;

namespace ALIN;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DispatcherQueue.TryEnqueue(async () => await StartenAsync());
    }

    private async System.Threading.Tasks.Task StartenAsync()
    {
        StatusText.Text = "Pruefe Werkzeuge...";
        var (ok, meldung) = await HealthcheckAusfuehrenAsync();
        StatusText.Text = ok ? "ALIN bereit." : $"Fehler: {meldung}";
        if (!ok)
        {
            var dialog = new Microsoft.UI.Xaml.Controls.ContentDialog
            {
                Title = "ALIN kann nicht starten",
                Content = meldung,
                CloseButtonText = "OK",
                XamlRoot = Content.XamlRoot,
            };
            await dialog.ShowAsync();
        }
    }

    private async System.Threading.Tasks.Task<(bool ok, string meldung)> HealthcheckAusfuehrenAsync()
    {
        var python = Path.Combine(AppContext.BaseDirectory, "Python312", "python.exe");
        var healthcheck = Path.Combine(AppContext.BaseDirectory, "alin_core", "healthcheck.py");

        if (!File.Exists(python))
            return (false, $"Python nicht gefunden: {python}");
        if (!File.Exists(healthcheck))
            return (false, $"Healthcheck nicht gefunden: {healthcheck}");

        var start = new System.Diagnostics.ProcessStartInfo(python, $"\"{healthcheck}\"")
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = AppContext.BaseDirectory,
        };

        using var proc = System.Diagnostics.Process.Start(start);
        if (proc == null) return (false, "Prozess konnte nicht gestartet werden");

        var stdout = await proc.StandardOutput.ReadToEndAsync();
        await proc.WaitForExitAsync();

        return proc.ExitCode == 0
            ? (true, "OK")
            : (false, $"Healthcheck fehlgeschlagen (Exit {proc.ExitCode}): {stdout[..Math.Min(200, stdout.Length)]}");
    }
}
