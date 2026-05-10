using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;

namespace KI_Legal_WindowsApp
{
    public partial class MainWindow : Window
    {
        private readonly string _root;
        private readonly string _logFile;

        public MainWindow()
        {
            InitializeComponent();

            _root = @"I:\KI_Legal_Project";
            _logFile = Path.Combine(_root, "Windows_App", "Logs", "APP_UI_LOG.txt");

            Directory.CreateDirectory(Path.GetDirectoryName(_logFile)!);

            AddLog("Anwendung gestartet.");
            AddLog("Projektwurzel: " + _root);

            StatusTextBlock.Text = "Bereit";
        }

        private void DokumenteLaden_Click(object sender, RoutedEventArgs e)
        {
            string sourceDocs = Path.Combine(_root, "Source_Docs");

            if (!Directory.Exists(sourceDocs))
            {
                AddLog("Ordner nicht gefunden: " + sourceDocs);
                StatusTextBlock.Text = "Source_Docs nicht gefunden";
                return;
            }

            var files = Directory.GetFiles(sourceDocs, "*.*", SearchOption.AllDirectories)
                .Select(f => new FileInfo(f))
                .Select(f => new DocumentRow
                {
                    Name = f.Name,
                    Extension = f.Extension,
                    SizeText = FormatSize(f.Length),
                    FullName = f.FullName
                })
                .ToList();

            DokumentenListe.ItemsSource = files;

            AddLog("Dokumente geladen: " + files.Count);
            StatusTextBlock.Text = "Dokumente geladen: " + files.Count;
        }

        private void AnalyseStarten_Click(object sender, RoutedEventArgs e)
        {
            AddLog("Analyse wurde angefordert. Die KI-Analyse wird im nächsten Ausbauschritt angebunden.");
            StatusTextBlock.Text = "Analyse vorbereitet";
        }

        private void ProtokollAnzeigen_Click(object sender, RoutedEventArgs e)
        {
            AddLog("Protokollanzeige angefordert.");

            if (File.Exists(_logFile))
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = _logFile,
                    UseShellExecute = true
                });
            }
        }

        private void Beenden_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void AddLog(string text)
        {
            string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " - " + text;

            LogTextBox.AppendText(line + Environment.NewLine);
            LogTextBox.ScrollToEnd();

            File.AppendAllText(_logFile, line + Environment.NewLine);
        }

        private static string FormatSize(long bytes)
        {
            if (bytes < 1024) return bytes + " B";
            if (bytes < 1024 * 1024) return Math.Round(bytes / 1024.0, 1) + " KB";
            return Math.Round(bytes / 1024.0 / 1024.0, 1) + " MB";
        }

        public sealed class DocumentRow
        {
            public string Name { get; set; } = "";
            public string Extension { get; set; } = "";
            public string SizeText { get; set; } = "";
            public string FullName { get; set; } = "";
        }
    }
}
