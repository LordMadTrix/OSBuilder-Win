using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace OSBuilderWinLauncher
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string appDir = AppDomain.CurrentDomain.BaseDirectory;
                string scriptPath = Path.Combine(appDir, "gui.py");

                if (!File.Exists(scriptPath))
                {
                    scriptPath = Path.GetFullPath(Path.Combine(appDir, "..", "gui.py"));
                }

                if (!File.Exists(scriptPath))
                {
                    MessageBox.Show(
                        "Fichier 'gui.py' introuvable dans le dossier :\n" + appDir,
                        "OSBuilder-Win - Erreur de Lancement",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                string pythonPath = FindPython();
                if (string.IsNullOrEmpty(pythonPath) || (!File.Exists(pythonPath) && !pythonPath.EndsWith(".exe")))
                {
                    MessageBox.Show(
                        "Environnement Python introuvable. Veuillez vérifier votre installation de Python 3.12.",
                        "OSBuilder-Win - Erreur Python",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pythonPath;
                psi.Arguments = string.Format("\"{0}\"", scriptPath);
                psi.WorkingDirectory = Path.GetDirectoryName(scriptPath);
                psi.UseShellExecute = true;
                psi.WindowStyle = ProcessWindowStyle.Normal;

                // Tente d'abord le lancement avec élévation UAC
                psi.Verb = "runas";

                try
                {
                    Process.Start(psi);
                }
                catch (System.ComponentModel.Win32Exception)
                {
                    // Si refus du prompt UAC, tentative en mode standard
                    psi.Verb = "";
                    Process.Start(psi);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Une erreur est survenue lors du démarrage d'OSBuilder-Win :\n\n" + ex.ToString(),
                    "OSBuilder-Win - Erreur Critique",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        static string FindPython()
        {
            // 1. Chemin direct de l'utilisateur (fiable à 100%)
            string explicitUserPyw = @"C:\Users\madtr\AppData\Local\Programs\Python\Python312\pythonw.exe";
            if (File.Exists(explicitUserPyw)) return explicitUserPyw;

            string explicitUserPy = @"C:\Users\madtr\AppData\Local\Programs\Python\Python312\python.exe";
            if (File.Exists(explicitUserPy)) return explicitUserPy;

            // 2. LocalAppData du profil courant
            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            if (!string.IsNullOrEmpty(localApp))
            {
                string p1 = Path.Combine(localApp, @"Programs\Python\Python312\pythonw.exe");
                if (File.Exists(p1)) return p1;

                string p2 = Path.Combine(localApp, @"Programs\Python\Python312\python.exe");
                if (File.Exists(p2)) return p2;
            }

            // 3. Recherche sous C:\Users\*\AppData\Local\Programs\Python
            try
            {
                if (Directory.Exists(@"C:\Users"))
                {
                    foreach (string uDir in Directory.GetDirectories(@"C:\Users"))
                    {
                        string candidate = Path.Combine(uDir, @"AppData\Local\Programs\Python\Python312\pythonw.exe");
                        if (File.Exists(candidate)) return candidate;
                    }
                }
            }
            catch { }

            // 4. Emplacements système standards
            string[] sysCandidates = new string[] {
                @"C:\Python312\pythonw.exe",
                @"C:\Python312\python.exe",
                @"C:\Python311\pythonw.exe",
                @"C:\Python311\python.exe",
                @"C:\Program Files\Python312\pythonw.exe",
                @"C:\Program Files\Python312\python.exe"
            };
            foreach (string c in sysCandidates)
            {
                if (File.Exists(c)) return c;
            }

            return "pythonw.exe";
        }
    }
}
