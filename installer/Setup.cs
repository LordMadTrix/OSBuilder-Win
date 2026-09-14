using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Win32;

namespace OSBuilderInstaller
{
    public class SetupForm : Form
    {
        private Label lblTitle;
        private Label lblSubtitle;
        private Label lblStatus;
        private ProgressBar progressBar;
        private CheckBox chkDesktopShortcut;
        private CheckBox chkStartMenuShortcut;
        private CheckBox chkLaunchNow;
        private Button btnInstall;
        private Button btnCancel;
        private Panel pnlHeader;

        public SetupForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Installation - OSBuilder-Win Studio v2.5 PRO";
            this.Size = new Size(560, 420);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(16, 20, 32);
            this.ForeColor = Color.FromArgb(240, 246, 252);
            this.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);

            string icoPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app.ico");
            if (File.Exists(icoPath))
            {
                try { this.Icon = new Icon(icoPath); } catch { }
            }

            // Header Panel
            pnlHeader = new Panel();
            pnlHeader.Dock = DockStyle.Top;
            pnlHeader.Height = 80;
            pnlHeader.BackColor = Color.FromArgb(8, 10, 15);

            lblTitle = new Label();
            lblTitle.Text = "OSBuilder-Win Studio v2.5 PRO";
            lblTitle.Font = new Font("Segoe UI", 14f, FontStyle.Bold);
            lblTitle.ForeColor = Color.FromArgb(0, 240, 255);
            lblTitle.Location = new Point(20, 15);
            lblTitle.AutoSize = true;

            lblSubtitle = new Label();
            lblSubtitle.Text = "Assistant d'Installation Officiel • Édition Signée LordMadTrix";
            lblSubtitle.Font = new Font("Segoe UI", 9f, FontStyle.Regular);
            lblSubtitle.ForeColor = Color.FromArgb(139, 155, 180);
            lblSubtitle.Location = new Point(22, 45);
            lblSubtitle.AutoSize = true;

            pnlHeader.Controls.Add(lblTitle);
            pnlHeader.Controls.Add(lblSubtitle);
            this.Controls.Add(pnlHeader);

            // Options
            Label lblDesc = new Label();
            lblDesc.Text = "Cet assistant va installer et configurer l'environnement OSBuilder-Win sur votre machine avec les raccourcis système, l'enregistrement Windows et les associations d'icônes.";
            lblDesc.Location = new Point(24, 95);
            lblDesc.Size = new Size(500, 45);
            this.Controls.Add(lblDesc);

            chkDesktopShortcut = new CheckBox();
            chkDesktopShortcut.Text = "Créer un raccourci sur le Bureau avec l'icône haute définition";
            chkDesktopShortcut.Checked = true;
            chkDesktopShortcut.Location = new Point(30, 150);
            chkDesktopShortcut.AutoSize = true;
            this.Controls.Add(chkDesktopShortcut);

            chkStartMenuShortcut = new CheckBox();
            chkStartMenuShortcut.Text = "Créer un raccourci dans le Menu Démarrer (Programmes)";
            chkStartMenuShortcut.Checked = true;
            chkStartMenuShortcut.Location = new Point(30, 180);
            chkStartMenuShortcut.AutoSize = true;
            this.Controls.Add(chkStartMenuShortcut);

            chkLaunchNow = new CheckBox();
            chkLaunchNow.Text = "Lancer OSBuilder-Win Studio dès la fin de l'installation";
            chkLaunchNow.Checked = true;
            chkLaunchNow.Location = new Point(30, 210);
            chkLaunchNow.AutoSize = true;
            this.Controls.Add(chkLaunchNow);

            // Progress Bar & Status
            progressBar = new ProgressBar();
            progressBar.Location = new Point(24, 255);
            progressBar.Size = new Size(500, 20);
            progressBar.Style = ProgressBarStyle.Blocks;
            progressBar.Visible = false;
            this.Controls.Add(progressBar);

            lblStatus = new Label();
            lblStatus.Text = "Prêt pour l'installation.";
            lblStatus.Location = new Point(24, 280);
            lblStatus.Size = new Size(500, 25);
            lblStatus.ForeColor = Color.FromArgb(0, 230, 118);
            this.Controls.Add(lblStatus);

            // Buttons
            btnInstall = new Button();
            btnInstall.Text = "⚡ Installer Maintenant";
            btnInstall.Size = new Size(180, 38);
            btnInstall.Location = new Point(200, 320);
            btnInstall.BackColor = Color.FromArgb(0, 240, 255);
            btnInstall.ForeColor = Color.FromArgb(8, 10, 15);
            btnInstall.FlatStyle = FlatStyle.Flat;
            btnInstall.Font = new Font("Segoe UI", 10f, FontStyle.Bold);
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);

            btnCancel = new Button();
            btnCancel.Text = "Fermer";
            btnCancel.Size = new Size(110, 38);
            btnCancel.Location = new Point(390, 320);
            btnCancel.BackColor = Color.FromArgb(22, 28, 46);
            btnCancel.ForeColor = Color.White;
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);
        }

        private void BtnInstall_Click(object sender, EventArgs e)
        {
            btnInstall.Enabled = false;
            progressBar.Visible = true;
            progressBar.Value = 20;
            lblStatus.Text = "Vérification des binaires et composants système...";
            Application.DoEvents();

            string currentDir = AppDomain.CurrentDomain.BaseDirectory;
            string exePath = Path.Combine(currentDir, "OSBuilder-Win.exe");
            string icoPath = Path.Combine(currentDir, "app.ico");
            string setupExe = Path.Combine(currentDir, "Setup.exe");

            progressBar.Value = 50;
            lblStatus.Text = "Génération des raccourcis Windows...";
            Application.DoEvents();

            // Création Raccourci Bureau
            if (chkDesktopShortcut.Checked && File.Exists(exePath))
            {
                string desktopFolder = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string lnkPath = Path.Combine(desktopFolder, "OSBuilder-Win.lnk");
                CreateShortcut(lnkPath, exePath, currentDir, icoPath, "OSBuilder-Win Studio - Constructeur d'ISOs Windows");
            }

            // Création Raccourci Menu Démarrer
            if (chkStartMenuShortcut.Checked && File.Exists(exePath))
            {
                string startMenu = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                string osbuilderStartDir = Path.Combine(startMenu, "OSBuilder-Win");
                Directory.CreateDirectory(osbuilderStartDir);
                string lnkPath = Path.Combine(osbuilderStartDir, "OSBuilder-Win Studio.lnk");
                CreateShortcut(lnkPath, exePath, currentDir, icoPath, "OSBuilder-Win Studio");
            }

            progressBar.Value = 80;
            lblStatus.Text = "Enregistrement dans le Registre Windows (Applications)...";
            Application.DoEvents();

            // Enregistrement dans HKCU Uninstall
            RegisterUninstallEntry(currentDir, exePath, icoPath, setupExe);

            progressBar.Value = 100;
            lblStatus.Text = "✅ Installation terminée avec succès !";
            lblStatus.ForeColor = Color.FromArgb(0, 240, 255);
            btnInstall.Text = "Terminé";

            MessageBox.Show(
                "OSBuilder-Win Studio v2.5 PRO a été configuré avec succès sur votre ordinateur !\n\n" +
                "• Raccourcis créés avec l'icône haute définition\n" +
                "• Enregistrement dans les Applications Windows effectué\n" +
                "• Moteur DISM et profils prêts à l'emploi",
                "Installation Réussie - LordMadTrix",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            );

            if (chkLaunchNow.Checked && File.Exists(exePath))
            {
                Process.Start(new ProcessStartInfo(exePath) { WorkingDirectory = currentDir });
            }

            this.Close();
        }

        private static void RegisterUninstallEntry(string installDir, string exePath, string iconPath, string setupExe)
        {
            try
            {
                using (RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\OSBuilder-Win"))
                {
                    if (key != null)
                    {
                        key.SetValue("DisplayName", "OSBuilder-Win Studio PRO");
                        key.SetValue("DisplayVersion", "2.5.0");
                        key.SetValue("Publisher", "LordMadTrix");
                        key.SetValue("InstallLocation", installDir);
                        key.SetValue("DisplayIcon", iconPath);
                        key.SetValue("UninstallString", "\"" + setupExe + "\" /uninstall");
                        key.SetValue("URLInfoAbout", "https://github.com/LordMadTrix/OSBuilder-Win");
                        key.SetValue("HelpLink", "https://github.com/LordMadTrix/OSBuilder-Win/issues");
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Erreur registre uninstall : " + ex.Message);
            }
        }

        public static void PerformUninstall()
        {
            try
            {
                // Supprimer raccourci bureau
                string desktopLnk = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "OSBuilder-Win.lnk");
                if (File.Exists(desktopLnk)) File.Delete(desktopLnk);

                // Supprimer menu démarrer
                string startMenuDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "OSBuilder-Win");
                if (Directory.Exists(startMenuDir)) Directory.Delete(startMenuDir, true);

                // Supprimer clé de registre
                Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\OSBuilder-Win", false);

                MessageBox.Show(
                    "Les raccourcis et l'enregistrement de OSBuilder-Win Studio ont été supprimés avec succès.",
                    "Désinstallation - LordMadTrix",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            catch (Exception ex)
            {
                MessageBox.Show("Erreur lors de la désinstallation : " + ex.Message, "Erreur", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string workingDir, string iconPath, string description)
        {
            try
            {
                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                dynamic shell = Activator.CreateInstance(shellType);
                dynamic shortcut = shell.CreateShortcut(shortcutPath);
                shortcut.TargetPath = targetPath;
                shortcut.WorkingDirectory = workingDir;
                shortcut.Description = description;
                if (File.Exists(iconPath))
                {
                    shortcut.IconLocation = iconPath + ",0";
                }
                shortcut.Save();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Erreur raccourci : " + ex.Message);
            }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            if (args != null && args.Length > 0 && args[0].ToLower() == "/uninstall")
            {
                PerformUninstall();
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}
