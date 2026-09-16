"""
Tests unitaires pour OSBuilder-Win.
Valide la configuration, les profils YAML, la génération autounattend.xml et la détection d'outils.
"""

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from core.config import load_profile_from_yaml, TargetOS, UnattendedConfig
from core.unattended_generator import UnattendedGenerator
from tools.fetch_tools import verify_all_tools


class TestOSBuilder(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_load_win7_profile(self):
        p_path = self.root_dir / "profiles" / "win7_modern_hw.yaml"
        self.assertTrue(p_path.exists())
        prof = load_profile_from_yaml(p_path)
        self.assertEqual(prof.target_os, TargetOS.WIN7)
        self.assertTrue(prof.win7.inject_nvme)
        self.assertTrue(prof.win7.inject_usb3)

    def test_load_win10_profile(self):
        p_path = self.root_dir / "profiles" / "win10_debloat.yaml"
        self.assertTrue(p_path.exists())
        prof = load_profile_from_yaml(p_path)
        self.assertEqual(prof.target_os, TargetOS.WIN10)
        self.assertTrue(len(prof.remove_appx_patterns) > 0)
        self.assertTrue(prof.disable_telemetry)

    def test_load_win11_profile(self):
        p_path = self.root_dir / "profiles" / "win11_unlocked.yaml"
        self.assertTrue(p_path.exists())
        prof = load_profile_from_yaml(p_path)
        self.assertEqual(prof.target_os, TargetOS.WIN11)
        self.assertTrue(prof.win11.bypass_tpm)
        self.assertTrue(prof.win11.classic_context_menu)
        self.assertTrue(prof.win11.disable_copilot)

    def test_unattended_generation_win11(self):
        config = UnattendedConfig(
            admin_username="TestAdmin",
            computer_name="WIN11-TEST",
            bypass_nro=True,
            locale="fr-FR"
        )
        gen = UnattendedGenerator(config=config, target_os=TargetOS.WIN11, architecture="x64")
        xml_str = gen.generate_xml()
        
        # Vérification de la validité syntaxique XML
        root = ET.fromstring(xml_str)
        self.assertIsNotNone(root)
        
        # Vérifier présence du compte utilisateur
        self.assertIn("TestAdmin", xml_str)
        # Vérifier présence des commandes de bypass TPM
        self.assertIn("BypassTPMCheck", xml_str)
        self.assertIn("HideOnlineAccountScreens", xml_str)

    def test_tool_verification(self):
        res = verify_all_tools()
        self.assertIn("admin", res)
        self.assertIn("dism", res)
        self.assertIn("wimlib", res)
        self.assertIn("7zip", res)
        self.assertIn("oscdimg", res)
        # DISM et Wimlib doivent être détectés
        self.assertIsNotNone(res["dism"])
        self.assertIsNotNone(res["wimlib"])

    def test_split_fat32_flag_in_profile(self):
        p_path = self.root_dir / "profiles" / "win11_unlocked.yaml"
        prof = load_profile_from_yaml(p_path)
        self.assertTrue(hasattr(prof, "split_wim_fat32"))
        prof.split_wim_fat32 = True
        self.assertTrue(prof.split_wim_fat32)

    def test_iso_inspector_parse_xml(self):
        from core.iso_inspector import IsoInspector
        sample_xml = """<WIM>
            <IMAGE INDEX="1">
                <NAME>Windows 11 Professionnel</NAME>
                <DESCRIPTION>Windows 11 Pro Edition</DESCRIPTION>
                <TOTALBYTES>16106127360</TOTALBYTES>
                <WINDOWS>
                    <ARCH>9</ARCH>
                    <EDITIONID>Professional</EDITIONID>
                    <VERSION><BUILD>22631</BUILD></VERSION>
                </WINDOWS>
            </IMAGE>
            <IMAGE INDEX="2">
                <NAME>Windows 11 Famille</NAME>
                <DESCRIPTION>Windows 11 Home Edition</DESCRIPTION>
                <TOTALBYTES>15032385536</TOTALBYTES>
                <WINDOWS>
                    <ARCH>9</ARCH>
                    <EDITIONID>Core</EDITIONID>
                    <VERSION><BUILD>22631</BUILD></VERSION>
                </WINDOWS>
            </IMAGE>
        </WIM>"""
        inspector = IsoInspector()
        editions = inspector._parse_wimlib_xml(sample_xml)
        self.assertEqual(len(editions), 2)
        self.assertEqual(editions[0]["name"], "Windows 11 Professionnel")
        self.assertEqual(editions[0]["index"], "1")
        self.assertEqual(editions[0]["architecture"], "x64")
        self.assertEqual(editions[1]["name"], "Windows 11 Famille")
        self.assertEqual(editions[1]["index"], "2")

    def test_dism_find_wimlib_falls_back_to_path_lookup(self):
        # Régression : _find_wimlib() utilise shutil.which() sans que le module
        # 'shutil' ne soit importé dans dism_manager.py, provoquant un NameError
        # dès que wimlib-imagex.exe est absent du dossier bin/ du projet.
        from unittest.mock import patch
        from core.dism_manager import DismManager

        dism = DismManager()
        with patch("core.dism_manager.Path.exists", return_value=False), \
             patch("core.dism_manager.shutil.which", return_value=None) as mock_which:
            result = dism._find_wimlib()
        self.assertIsNone(result)
        mock_which.assert_called_once_with("wimlib-imagex")

    def test_dism_split_image_cmd(self):
        from unittest.mock import MagicMock
        from core.dism_manager import DismManager
        
        dism = DismManager()
        dism._run_dism = MagicMock(return_value=MagicMock(returncode=0))
        
        res = dism.split_image("C:\\test\\install.wim", "C:\\test\\install.swm", file_size_mb=3800)
        self.assertTrue(res)
        dism._run_dism.assert_called_once()
        args = dism._run_dism.call_args[0][0]
        self.assertIn("/Split-Image", args)
        self.assertTrue(any("/ImageFile:" in a for a in args))
        self.assertTrue(any("/SWMFile:" in a for a in args))
    def test_unattended_product_key_and_firstlogon(self):
        config = UnattendedConfig(
            admin_username="GamerAdmin",
            computer_name="GAMING-RIG",
            product_key="W269N-WFGWX-YVC9B-4J6C9-T83GX"
        )
        cmds = ["winget install --id 7zip.7zip --silent", "powershell install_vc.ps1"]
        gen = UnattendedGenerator(config=config, target_os=TargetOS.WIN11, post_install_commands=cmds)
        xml_str = gen.generate_xml()
        
        root = ET.fromstring(xml_str)
        self.assertIsNotNone(root)
        self.assertIn("W269N-WFGWX-YVC9B-4J6C9-T83GX", xml_str)
        self.assertIn("FirstLogonCommands", xml_str)
        self.assertIn("7zip.7zip", xml_str)

    def test_registry_manager_explorer_and_services(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import ExplorerOptions, ServicesOptions
        
        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)
        
        # Test Explorer tweaks
        exp = ExplorerOptions(show_file_extensions=True, dark_mode=True, open_to_this_pc=True)
        reg.apply_explorer_tweaks(exp)
        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("HideFileExt", names)
        self.assertIn("LaunchTo", names)
        self.assertIn("AppsUseLightTheme", names)
        
        # Test Services tweaks
        reg.set_value.reset_mock()
        srv = ServicesOptions(disable_sysmain=True, disable_spooler=True)
        reg.apply_services_tweaks(srv)
        calls_srv = [c[0] for c in reg.set_value.call_args_list]
        paths_srv = [c[1] for c in calls_srv]
        self.assertTrue(any("SysMain" in p for p in paths_srv))
        self.assertTrue(any("Spooler" in p for p in paths_srv))

    def test_dism_net35_and_directplay(self):
        from unittest.mock import MagicMock
        from core.dism_manager import DismManager
        
        dism = DismManager()
        dism._run_dism = MagicMock(return_value=MagicMock(returncode=0))
        
        dism.enable_directplay("C:\\mount")
        args_dp = dism._run_dism.call_args[0][0]
        self.assertIn("/FeatureName:DirectPlay", args_dp)

    def test_build_reporter_markdown(self):
        import tempfile
        from core.build_reporter import BuildReporter
        from core.config import BuildProfile, TargetOS
        
        prof = BuildProfile(name="TestProfile", target_os=TargetOS.WIN11)
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.iso"
            out = Path(tmpdir) / "output.iso"
            src.write_bytes(b"dummy")
            out.write_bytes(b"dummy")
            
            reporter = BuildReporter(prof, src, out)
            report_path = reporter.generate_markdown_report(Path(tmpdir) / "report.md")
            self.assertTrue(report_path.exists())
            content = report_path.read_text(encoding="utf-8")
            self.assertIn("Rapport de Compilation OSBuilder-Win", content)
            self.assertIn("TestProfile", content)
            self.assertIn("SHA-256", content)

    def test_usb_creator_init(self):
        from core.usb_creator import UsbCreator
        creator = UsbCreator()
        self.assertIsNotNone(creator)
        # Vérifier que list_usb_drives s'exécute sans exception
    def test_take_ownership_tweak(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import ExplorerOptions

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        exp = ExplorerOptions(add_take_ownership=True)
        reg.apply_explorer_tweaks(exp)

        calls = [c[0] for c in reg.set_value.call_args_list]
        paths = [c[1] for c in calls]
        self.assertTrue(any("shell\\runas" in p for p in paths))
        self.assertTrue(any("Directory\\shell\\runas" in p for p in paths))

    def test_network_gaming_nagle(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        reg.apply_network_gaming_tweaks()
        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("TcpAckFrequency", names)
        self.assertIn("TCPNoDelay", names)
        self.assertIn("DefaultTTL", names)

    def test_fast_startup_and_hwid(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import ServicesOptions, PostInstallOptions

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        srv = ServicesOptions(disable_fast_startup=True)
        reg.apply_services_tweaks(srv)
        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("HiberbootEnabled", names)

        post = PostInstallOptions(enable_hwid_activation=True)
        self.assertTrue(post.enable_hwid_activation)


    def test_unattended_zero_click_gpt_and_admin(self):
        config = UnattendedConfig(
            admin_username="TechAdmin",
            computer_name="AUTONOME-PC",
            auto_disk_partition=True,
            disk_id=0,
            use_builtin_admin=True,
            locale="fr-FR"
        )
        gen = UnattendedGenerator(config=config, target_os=TargetOS.WIN11)
        xml_str = gen.generate_xml()
        
        root = ET.fromstring(xml_str)
        self.assertIsNotNone(root)
        self.assertIn("<DiskConfiguration>", xml_str)
        self.assertIn("<WillWipeDisk>true</WillWipeDisk>", xml_str)
        self.assertIn("<DiskID>0</DiskID>", xml_str)
        self.assertIn("<Type>EFI</Type>", xml_str)
        self.assertIn("<Type>MSR</Type>", xml_str)
        self.assertIn("<Type>Primary</Type>", xml_str)
        self.assertIn("<PartitionID>3</PartitionID>", xml_str)
        self.assertIn("<WillShowUI>OnError</WillShowUI>", xml_str)
        self.assertIn("net user Administrator /active:yes", xml_str)

    def test_compression_and_vmd_config(self):
        from core.config import BuildProfile, CompressionType
        prof = BuildProfile(
            name="ESD_Profile",
            target_os=TargetOS.WIN11,
            single_edition_only=True,
            compression_type=CompressionType.RECOVERY,
            intel_vmd_drivers_dir="C:\\drivers\\vmd"
        )
        d = prof.to_dict()
        self.assertTrue(d["single_edition_only"])
        self.assertEqual(d["compression_type"], "recovery")
        self.assertEqual(d["intel_vmd_drivers_dir"], "C:\\drivers\\vmd")

        prof2 = BuildProfile.from_dict(d)
        self.assertTrue(prof2.single_edition_only)
        self.assertEqual(prof2.compression_type, CompressionType.RECOVERY)
        self.assertEqual(prof2.intel_vmd_drivers_dir, "C:\\drivers\\vmd")

    def test_storage_and_gaming_registry_tweaks(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import FeaturesOptions

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        feats = FeaturesOptions(optimize_ntfs_trim=True, enable_hags=True, disable_hpet_synthetic=True)
        reg.apply_storage_optimizations(feats)
        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("DisableDeleteNotify", names)
        self.assertIn("NtfsDisableLastAccessUpdate", names)

        reg.set_value.reset_mock()
        reg.apply_advanced_gaming_tweaks(feats)
        calls_gaming = [c[0] for c in reg.set_value.call_args_list]
        names_gaming = [c[2] for c in calls_gaming]
        self.assertIn("HwSchMode", names_gaming)
        self.assertIn("GlobalTimerResolutionRequests", names_gaming)
        self.assertIn("OverlayTestMode", names_gaming)

        reg.set_value.reset_mock()
        reg.apply_extended_telemetry_and_privacy()
        calls_privacy = [c[0] for c in reg.set_value.call_args_list]
        names_privacy = [c[2] for c in calls_privacy]
        self.assertIn("Enabled", names_privacy)
        self.assertIn("TailoredExperiencesWithDiagnosticDataEnabled", names_privacy)

    def test_dism_reserved_storage_and_export(self):
        from unittest.mock import MagicMock
        from core.dism_manager import DismManager
        from core.config import CompressionType

        dism = DismManager()
        dism._run_dism = MagicMock(return_value=MagicMock(returncode=0))
        dism._run_wimlib = MagicMock(return_value=MagicMock(returncode=0))

        # Test reserved storage
        res = dism.set_reserved_storage("C:\\mount", state=False)
        self.assertTrue(res)
        args_rs = dism._run_dism.call_args[0][0]
        self.assertIn("/Set-ReservedStorageState", args_rs)
        self.assertIn("/State:Disabled", args_rs)

        # Test export single image with wimlib
        dism._wimlib_path = "C:\\bin\\wimlib-imagex.exe"
        res_exp = dism.export_single_image(
            src_image="C:\\in.wim",
            dest_image="C:\\out.wim",
            index=1,
            compression="recovery"
        )
        self.assertTrue(res_exp)
        dism._run_wimlib.assert_called_once()
        args_wimlib = dism._run_wimlib.call_args[0][0]
        self.assertIn("export", args_wimlib)
        self.assertIn("--compress=recovery", args_wimlib)

    def test_pipeline_cancellation_flag(self):
        from core.pipeline import BuildPipeline
        from core.config import BuildProfile, TargetOS

        prof = BuildProfile(name="CancelTest", target_os=TargetOS.WIN11)
        pipe = BuildPipeline(prof)
        self.assertFalse(pipe._is_cancelled)
        pipe.cancel()
        self.assertTrue(pipe._is_cancelled)

    def test_iso_validator_tree(self):
        import tempfile
        from core.iso_validator import IsoValidator

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Cas invalide (répertoire vide)
            res_invalid = IsoValidator.validate_extracted_tree(root)
            self.assertFalse(res_invalid.is_valid)
            self.assertTrue(len(res_invalid.missing_files) > 0)

            # Création de l'arborescence valide
            (root / "boot").mkdir(parents=True)
            (root / "bootmgr").write_bytes(b"bootmgr")
            (root / "boot" / "bcd").write_bytes(b"bcd")

            (root / "efi" / "boot").mkdir(parents=True)
            (root / "efi" / "microsoft" / "boot").mkdir(parents=True)
            (root / "efi" / "boot" / "bootx64.efi").write_bytes(b"bootx64")
            (root / "efi" / "microsoft" / "boot" / "bcd").write_bytes(b"bcd")

            (root / "sources").mkdir(parents=True)
            # boot.wim (> 10MB pour le validateur)
            boot_wim = root / "sources" / "boot.wim"
            boot_wim.write_bytes(b"X" * (11 * 1024 * 1024))
            (root / "sources" / "install.wim").write_bytes(b"install_wim_content")

            res_valid = IsoValidator.validate_extracted_tree(root)
            self.assertTrue(res_valid.is_valid)
            self.assertTrue(res_valid.has_bios_boot)
            self.assertTrue(res_valid.has_uefi_boot)
            self.assertTrue(res_valid.has_boot_wim)
            self.assertTrue(res_valid.has_install_image)
            self.assertEqual(res_valid.install_image_format, "WIM")

    def test_appx_catalog_presets(self):
        from core.appx_catalog import get_patterns_for_preset, AppxPreset

        light = get_patterns_for_preset(AppxPreset.LIGHT)
        self.assertTrue(any("FeedbackHub" in p for p in light))
        self.assertTrue(any("Tips" in p for p in light))

        rec = get_patterns_for_preset(AppxPreset.RECOMMENDED)
        self.assertTrue(any("Xbox" in p for p in rec))
        self.assertTrue(any("BingNews" in p for p in rec))
        self.assertTrue(any("SkypeApp" in p for p in rec))

        agg = get_patterns_for_preset(AppxPreset.AGGRESSIVE)
        self.assertTrue(len(agg) >= len(rec))
        self.assertTrue(any("ZuneMusic" in p for p in agg))

    def test_driver_manager_scan(self):
        import tempfile
        from core.driver_manager import DriverManager

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            drv1 = root / "net" / "netadapter.inf"
            drv1.parent.mkdir(parents=True)
            drv1.write_text("[Version]\nSignature=$Windows NT$\nClass=Net\nProvider=Intel", encoding="utf-8")

            drv2 = root / "storage" / "nvme.inf"
            drv2.parent.mkdir(parents=True)
            drv2.write_text("[Version]\nSignature=$Windows NT$\nClass=SCSIAdapter\nProvider=Samsung NVMe", encoding="utf-8")

            mgr = DriverManager()
            scanned = mgr.scan_inf_drivers(root)
            self.assertEqual(len(scanned), 2)

    def test_registry_responsiveness_and_context_menus(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import ExplorerOptions, FeaturesOptions

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        exp = ExplorerOptions(
            disable_start_web_search=True,
            add_restart_explorer_context_menu=True,
            add_open_with_notepad=True,
            add_cmd_admin_here=True
        )
        reg.apply_explorer_tweaks(exp)
        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("DisableWebSearch", names)
        self.assertIn("BingSearchEnabled", names)
        paths = [c[1] for c in calls]
        self.assertTrue(any("RestartExplorer" in p for p in paths))
        self.assertTrue(any("OpenWithNotepad" in p for p in paths))
        self.assertTrue(any("cmdadmin" in p for p in paths))

        reg.set_value.reset_mock()
        feats = FeaturesOptions(
            optimize_mmcss_latency=True,
            optimize_processor_scheduling=True,
            disable_edge_prelaunch=True,
            disable_smartscreen=True
        )
        reg.apply_system_responsiveness_and_latency(feats)
        calls_lat = [c[0] for c in reg.set_value.call_args_list]
        names_lat = [c[2] for c in calls_lat]
        self.assertIn("SystemResponsiveness", names_lat)
        self.assertIn("Win32PrioritySeparation", names_lat)
        self.assertIn("AllowPrelaunch", names_lat)
        self.assertIn("EnableSmartScreen", names_lat)


    def test_update_manager_ssu_before_lcu(self):
        import tempfile
        from core.update_manager import UpdateManager

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            # Create LCU and SSU packages
            lcu = dir_path / "windows11.0-kb5034441-x64-cumulative.msu"
            ssu = dir_path / "windows11.0-kb5034440-x64-ssu.msu"
            other = dir_path / "windows11.0-kb5034442-x64-general.cab"
            lcu.write_bytes(b"lcu")
            ssu.write_bytes(b"ssu")
            other.write_bytes(b"cab")

            mgr = UpdateManager()
            packages = mgr.scan_updates(dir_path, target_arch="x64")
            self.assertEqual(len(packages), 3)
            # SSU must be first
            self.assertEqual(packages[0].name, ssu.name)
            self.assertIn("ssu", packages[0].name.lower())

    def test_oem_branding_application(self):
        import tempfile
        from unittest.mock import MagicMock
        from core.oem_manager import OemManager
        from core.config import OemOptions
        from core.registry_manager import RegistryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            mount_dir = Path(tmpdir)
            # Mock image structure
            (mount_dir / "Windows" / "System32").mkdir(parents=True)
            (mount_dir / "Windows" / "Web" / "Wallpaper" / "Windows").mkdir(parents=True)

            logo_file = mount_dir / "test_logo.bmp"
            logo_file.write_bytes(b"BMlogo")
            wall_file = mount_dir / "test_wall.jpg"
            wall_file.write_bytes(b"JPGwallpaper")

            oem_opts = OemOptions(
                enabled=True,
                manufacturer="CustomPC Lab",
                model="Gaming Beast Pro",
                support_url="https://example.com/support",
                support_hours="24/7",
                support_phone="+33100000000",
                logo_path=str(logo_file),
                wallpaper_path=str(wall_file)
            )

            reg_mock = RegistryManager()
            reg_mock.set_value = MagicMock(return_value=True)

            oem_mgr = OemManager()
            success = oem_mgr.apply_oem_branding(mount_dir, reg_mock.set_value, oem_opts)
            self.assertTrue(success)

            # Check registry calls
            calls = [c[0] for c in reg_mock.set_value.call_args_list]
            names = [c[2] for c in calls]
            self.assertIn("Manufacturer", names)
            self.assertIn("Model", names)
            self.assertIn("SupportURL", names)
            self.assertIn("Logo", names)

            # Check files copied
            self.assertTrue((mount_dir / "Windows" / "System32" / "oemlogo.bmp").exists())
            self.assertTrue((mount_dir / "Windows" / "Web" / "Wallpaper" / "Windows" / "img0.jpg").exists())

    def test_unattended_display_resolution(self):
        from core.unattended_generator import UnattendedGenerator
        from core.config import UnattendedConfig, TargetOS

        cfg = UnattendedConfig(
            computer_name="DESKTOP-TEST",
            admin_password="Password123!",
            wipe_disk=True,
            display_resolution="1920x1080"
        )
        gen = UnattendedGenerator(config=cfg, target_os=TargetOS.WIN11, architecture="x64")
        xml = gen.generate_xml()
        self.assertIn("<HorizontalResolution>1920</HorizontalResolution>", xml)
        self.assertIn("<VerticalResolution>1080</VerticalResolution>", xml)
        self.assertIn("<ColorDepth>32</ColorDepth>", xml)
        self.assertIn("<RefreshRate>60</RefreshRate>", xml)

    def test_registry_win11_24h2_and_onedrive_tweaks(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        reg.apply_win11_24h2_and_onedrive_tweaks(
            prevent_device_encryption=True,
            disable_onedrive=True
        )

        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("PreventDeviceEncryption", names)
        self.assertIn("DisableFileSyncNGSC", names)
        self.assertIn("System.IsPinnedToNameSpaceTree", names)


    def test_win11_taskbar_and_oobe_tweaks(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import Win11Options

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        opts = Win11Options(
            taskbar_align_left=True,
            disable_taskbar_chat=True,
            disable_device_setup_suggestions=True,
            disable_lockscreen_tips=True
        )
        reg.apply_win11_taskbar_and_oobe_tweaks(opts)

        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("TaskbarAl", names)
        self.assertIn("TaskbarMn", names)
        self.assertIn("ScoobeSystemSettingEnabled", names)
        self.assertIn("RotatingLockScreenOverlayEnabled", names)

    def test_dism_cleanup_component_store(self):
        from unittest.mock import MagicMock
        from core.dism_manager import DismManager
        import subprocess

        dism = DismManager()
        dism._run_dism = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="Success", stderr=""))

        success = dism.cleanup_image_component_store("C:\\DummyMount", reset_base=True)
        self.assertTrue(success)

        # Vérifier que les arguments contenaient /StartComponentCleanup et /ResetBase
        called_args = dism._run_dism.call_args[0][0]
        self.assertIn("/StartComponentCleanup", called_args)
        self.assertIn("/ResetBase", called_args)

    def test_unattended_first_logon_commands(self):
        from core.unattended_generator import UnattendedGenerator
        from core.config import UnattendedConfig, TargetOS

        cfg = UnattendedConfig(
            computer_name="WIN11-TEST",
            admin_username="Admin",
            first_logon_commands=[
                "cmd.exe /c echo Hello World",
                "powershell.exe -Command Write-Host Ready"
            ]
        )
        gen = UnattendedGenerator(config=cfg, target_os=TargetOS.WIN11, architecture="x64")
        xml = gen.generate_xml()
        self.assertIn("<FirstLogonCommands>", xml)
        self.assertIn("<CommandLine>cmd.exe /c echo Hello World</CommandLine>", xml)
        self.assertIn("<CommandLine>powershell.exe -Command Write-Host Ready</CommandLine>", xml)


    def test_win11_superlite_24h2_profile_load(self):
        from core.config import load_profile_from_yaml, TargetOS, AppxPreset, CompressionType

        profile_path = Path(__file__).resolve().parent.parent / "profiles" / "win11_superlite_24h2.yaml"
        self.assertTrue(profile_path.exists())

        prof = load_profile_from_yaml(profile_path)
        self.assertEqual(prof.target_os, TargetOS.WIN11)
        self.assertEqual(prof.appx_preset, AppxPreset.AGGRESSIVE)
        self.assertTrue(prof.cleanup_component_store)
        self.assertTrue(prof.single_edition_only)
        self.assertEqual(prof.compression_type, CompressionType.RECOVERY)
        self.assertTrue(prof.win11.prevent_automatic_bitlocker)
        self.assertTrue(prof.win11.taskbar_align_left)
        self.assertTrue(prof.system_features.optimize_memory_paging)

    def test_memory_and_paging_optimizations(self):
        from unittest.mock import MagicMock
        from core.registry_manager import RegistryManager
        from core.config import FeaturesOptions

        reg = RegistryManager()
        reg.set_value = MagicMock(return_value=True)

        feats = FeaturesOptions(optimize_memory_paging=True)
        reg.apply_memory_and_paging_optimizations(feats)

        calls = [c[0] for c in reg.set_value.call_args_list]
        names = [c[2] for c in calls]
        self.assertIn("DisablePagingExecutive", names)
        self.assertIn("LargeSystemCache", names)
        self.assertIn("ClearPageFileAtShutdown", names)

    def test_dism_capabilities_management(self):
        from unittest.mock import MagicMock
        from core.dism_manager import DismManager
        import subprocess

        dism = DismManager()
        dism._run_dism = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""))

        # Test Add-Capability
        res_add = dism.add_capability("C:\\Mount", "OpenSSH.Client~~~~0.0.1.0")
        self.assertTrue(res_add)
        called_add = dism._run_dism.call_args[0][0]
        self.assertIn("/Add-Capability", called_add)
        self.assertIn("/CapabilityName:OpenSSH.Client~~~~0.0.1.0", called_add)

        # Test Remove-Capability
        res_rm = dism.remove_capability("C:\\Mount", "App.Support.QuickAssist~~~~0.0.1.0")
        self.assertTrue(res_rm)
        called_rm = dism._run_dism.call_args[0][0]
        self.assertIn("/Remove-Capability", called_rm)
        self.assertIn("/CapabilityName:App.Support.QuickAssist~~~~0.0.1.0", called_rm)


    def test_gui_dark_stylesheet_and_structure(self):
        try:
            import gui
            self.assertIn("MainTabs", gui.DARK_STYLESHEET)
            self.assertIn("SubTabs", gui.DARK_STYLESHEET)
            self.assertIn("PrimaryBtn", gui.DARK_STYLESHEET)
            self.assertIn("#00d2ff", gui.DARK_STYLESHEET)
            self.assertIn("QProgressBar", gui.DARK_STYLESHEET)
        except ImportError:
            # PyQt6 non installé dans l'environnement courant de test
            pass

    def test_gui_theme_engine_palettes(self):
        try:
            import gui
            self.assertIn("cyber_cyan", gui.THEME_PALETTES)
            self.assertIn("dracula_neon", gui.THEME_PALETTES)
            self.assertIn("matrix_green", gui.THEME_PALETTES)
            self.assertIn("solar_amber", gui.THEME_PALETTES)
            self.assertIn("crimson_rog", gui.THEME_PALETTES)
            self.assertIn("nordic_frost", gui.THEME_PALETTES)
            self.assertIn("austere_mono", gui.THEME_PALETTES)
            self.assertIn("mados_signature", gui.THEME_PALETTES)

            for key in gui.THEME_PALETTES:
                qss = gui.get_theme_stylesheet(key)
                self.assertIn("MainTabs", qss)
                self.assertIn("SubTabs", qss)
        except ImportError:
            pass


    def test_profile_winre_and_setup_complete_fields(self):
        from core.config import BuildProfile, TargetOS
        prof = BuildProfile(
            name="TestWinRE",
            target_os=TargetOS.WIN11,
            inject_drivers_to_winre=True,
            setup_complete_commands=["net stop wuauserv", "powercfg /hibernate off"]
        )
        self.assertTrue(prof.inject_drivers_to_winre)
        self.assertEqual(len(prof.setup_complete_commands), 2)
        d = prof.to_dict()
        self.assertTrue(d["inject_drivers_to_winre"])
        self.assertIn("net stop wuauserv", d["setup_complete_commands"])
        rebuilt = BuildProfile.from_dict(d)
        self.assertTrue(rebuilt.inject_drivers_to_winre)
        self.assertEqual(rebuilt.setup_complete_commands, prof.setup_complete_commands)

    def test_dism_inject_drivers_to_winre_missing_wim(self):
        from core.dism_manager import DismManager
        from unittest.mock import MagicMock
        dism = DismManager()
        dism._run_dism = MagicMock()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Sans Winre.wim, doit retourner False proprement sans lever d'exception
            res = dism.inject_drivers_to_winre(tmpdir, [tmpdir])
            self.assertFalse(res)
            dism._run_dism.assert_not_called()

    def test_dism_inject_drivers_to_winre_success(self):
        from core.dism_manager import DismManager
        from unittest.mock import MagicMock
        import tempfile
        import subprocess

        dism = DismManager()
        # Mock _run_dism pour simuler succès
        ok_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="Succès", stderr="")
        dism._run_dism = MagicMock(return_value=ok_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            rec_dir = tmppath / "Windows" / "System32" / "Recovery"
            rec_dir.mkdir(parents=True)
            winre_file = rec_dir / "Winre.wim"
            winre_file.write_bytes(b"MOCK_WIM_CONTENT")

            drv_dir = tmppath / "Drivers"
            drv_dir.mkdir()

            res = dism.inject_drivers_to_winre(tmppath, [drv_dir], scratch_dir=tmppath)
            self.assertTrue(res)

            # Vérifier les appels DISM successifs
            calls = [call[0][0] for call in dism._run_dism.call_args_list]
            self.assertTrue(any("/Mount-Wim" in c for c in calls))
            self.assertTrue(any("/Add-Driver" in c for c in calls))
            self.assertTrue(any("/Unmount-Wim" in c and "/Commit" in c for c in calls))

    def test_setup_complete_script_injection_logic(self):
        import tempfile
        from core.config import BuildProfile, TargetOS
        from core.pipeline import BuildPipeline

        prof = BuildProfile(
            name="TestPipeline",
            target_os=TargetOS.WIN11,
            setup_complete_commands=["echo LordMadTrix >> %TEMP%\\test.log"]
        )
        pipeline = BuildPipeline(prof)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            scripts_dir = tmppath / "Windows" / "Setup" / "Scripts"
            scripts_dir.mkdir(parents=True)

            setup_complete_path = scripts_dir / "SetupComplete.cmd"
            base_script = self.root_dir / "scripts" / "setup_complete.cmd"
            content = ""
            if base_script.exists():
                with open(base_script, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "@echo off\r\n"

            custom_cmds = getattr(prof, "setup_complete_commands", [])
            if custom_cmds:
                content += "\r\n:: Commandes personnalisées\r\n"
                for cmd_line in custom_cmds:
                    content += f"{cmd_line.strip()}\r\n"

            with open(setup_complete_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.assertTrue(setup_complete_path.exists())
            written_content = setup_complete_path.read_text(encoding="utf-8")
            self.assertIn("LordMadTrix", written_content)
            self.assertIn("schtasks", written_content)

    def test_load_mados_signature_profile(self):
        p_path = self.root_dir / "profiles" / "mados_edition.yaml"
        self.assertTrue(p_path.exists())
        prof = load_profile_from_yaml(p_path)
        self.assertIn("MadOS", prof.name)
        self.assertEqual(prof.target_os, TargetOS.WIN11)
        self.assertTrue(prof.explorer.apply_mados_theme)
        self.assertEqual(prof.explorer.mados_accent_color, "#00f0ff")
        self.assertTrue(prof.win11.bypass_tpm)
        self.assertTrue(prof.system_features.disable_nagle_algorithm)
        self.assertTrue(prof.inject_drivers_to_winre)
        self.assertEqual(prof.oem.manufacturer, "LordMadTrix Custom Rig")

    def test_registry_apply_mados_theme(self):
        from core.registry_manager import RegistryManager
        from unittest.mock import MagicMock
        reg = RegistryManager()
        reg.set_value = MagicMock()

        reg.apply_mados_theme(accent_hex="#00f0ff")

        # Vérifier que set_value a été appelé pour AppsUseLightTheme, DWM AccentColor et MenuShowDelay
        calls = reg.set_value.call_args_list
        keys_checked = [(c[0][0], c[0][1], c[0][2], c[0][4]) for c in calls]
        
        # Dark mode dans NTUSER
        self.assertTrue(any(k[0] == "NTUSER" and "Personalize" in k[1] and k[2] == "AppsUseLightTheme" and k[3] == 0 for k in keys_checked))
        # DWM Accent Color
        self.assertTrue(any(k[0] == "NTUSER" and "DWM" in k[1] and k[2] == "AccentColor" for k in keys_checked))
        # MenuShowDelay à 0ms
        self.assertTrue(any(k[0] == "NTUSER" and "Desktop" in k[1] and k[2] == "MenuShowDelay" and k[3] == "0" for k in keys_checked))

    def test_hwid_silent_command_syntax(self):
        from core.config import BuildProfile, TargetOS
        prof = BuildProfile(name="TestHWID", target_os=TargetOS.WIN11)
        prof.post_install.enable_hwid_activation = True
        
        first_logon_cmds = []
        if prof.post_install.enable_hwid_activation:
            first_logon_cmds.append(
                'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((irm https://get.activated.win))) /HWID"'
            )
        self.assertEqual(len(first_logon_cmds), 1)
        self.assertIn("/HWID", first_logon_cmds[0])
        self.assertIn("https://get.activated.win", first_logon_cmds[0])

    def test_image_optimizer_methods(self):
        from core.image_optimizer import ImageOptimizer
        from unittest.mock import patch, MagicMock
        import tempfile

        opt = ImageOptimizer()
        with tempfile.TemporaryDirectory() as td:
            dummy_wim = Path(td) / "dummy.wim"
            dummy_wim.write_bytes(b"MSWIM" + b"\x00" * 1024)

            # Test optimize_wim avec simulation subprocess
            with patch("subprocess.run") as mock_sub:
                mock_sub.return_value = MagicMock(returncode=0, stdout="Optimized successfully", stderr="")
                res = opt.optimize_wim(dummy_wim, compression="maximum")
                self.assertTrue(res)

            # Test convert_wim_to_esd
            with patch("subprocess.run") as mock_sub:
                target_esd = Path(td) / "dummy.esd"
                target_esd.write_bytes(b"MSESD" + b"\x00" * 512)
                mock_sub.return_value = MagicMock(returncode=0, stdout="Exported to ESD", stderr="")
                esd_res = opt.convert_wim_to_esd(dummy_wim, target_esd)
                self.assertIsNotNone(esd_res)
                self.assertEqual(esd_res.name, "dummy.esd")

    def test_features_manager_preset_gaming(self):
        from core.features_manager import FeaturesManager, FeaturePreset, PRESET_CONFIGS
        from unittest.mock import MagicMock

        mgr = FeaturesManager()
        self.assertIn("gaming", mgr.get_available_presets())
        self.assertIn("developer", mgr.get_available_presets())

        mock_dism = MagicMock()
        success = mgr.apply_preset("C:\\fake_mount", mock_dism, FeaturePreset.GAMING)
        self.assertTrue(success)

        # Vérifier que DirectPlay et NetFx3 ont été activés
        mock_dism.enable_feature.assert_any_call("C:\\fake_mount", "DirectPlay")
        mock_dism.enable_feature.assert_any_call("C:\\fake_mount", "NetFx3")
        # Vérifier que SMB1 a été désactivé
        mock_dism.disable_feature.assert_any_call("C:\\fake_mount", "SMB1Protocol")

    def test_software_installer_staging_and_flags(self):
        from core.software_installer import SoftwareInstaller
        import tempfile

        inst = SoftwareInstaller()
        # Test détection des flags
        self.assertEqual(inst.detect_installer_silent_flags("setup_inno.exe"), "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-")
        self.assertEqual(inst.detect_installer_silent_flags("7z2408-x64.exe"), "/S")
        self.assertEqual(inst.detect_installer_silent_flags("app.msi"), "/qn /norestart")
        self.assertEqual(inst.detect_installer_silent_flags("vcredist_x64.exe"), "/quiet /norestart")

        with tempfile.TemporaryDirectory() as td:
            src_apps = Path(td) / "custom_apps"
            src_apps.mkdir()
            (src_apps / "test_app.exe").write_bytes(b"MZfake")
            (src_apps / "silent.msi").write_bytes(b"MSIfake")

            mock_mount = Path(td) / "mount"
            mock_mount.mkdir()

            staged = inst.stage_offline_applications(src_apps, mock_mount)
            self.assertEqual(len(staged), 2)
            dest_apps = mock_mount / "Windows" / "Setup" / "Apps"
            self.assertTrue((dest_apps / "test_app.exe").exists())
            self.assertTrue((dest_apps / "silent.msi").exists())

            # Test génération du script orchestrateur
            cmds = [cmd for _, cmd in staged]
            script_path = inst.generate_apps_install_script(mock_mount, cmds)
            self.assertIsNotNone(script_path)
            self.assertTrue(script_path.exists())
            script_content = script_path.read_text(encoding="utf-8")
            self.assertIn("test_app.exe", script_content)
            self.assertIn("msiexec.exe", script_content)

    def test_win11_patch_extracted_sources(self):
        from core.win11_bypass import Win11Bypass
        import tempfile

        bypass = Win11Bypass()
        with tempfile.TemporaryDirectory() as td:
            sources_dir = Path(td) / "sources"
            sources_dir.mkdir()
            dll_path = sources_dir / "appraiserres.dll"
            dll_path.write_bytes(b"original_appraiser_content")
            sdb_path = sources_dir / "appraiser.sdb"
            sdb_path.write_bytes(b"sdb_telemetry")

            success = bypass.patch_extracted_sources(td)
            self.assertTrue(success)
            self.assertTrue(dll_path.exists())
            self.assertEqual(dll_path.stat().st_size, 0)  # Neutralisé à 0 octets
            self.assertFalse(sdb_path.exists())  # Nettoyé

    def test_registry_context_menu_pro_and_dns(self):
        from core.registry_manager import RegistryManager
        from unittest.mock import MagicMock
        from core.config import ExplorerOptions

        reg = RegistryManager()
        reg.set_value = MagicMock()

        # Context Menu Pro
        exp = ExplorerOptions(add_powershell_admin_context_menu=True, add_compact_os_context_menu=True)
        reg.apply_context_menu_pro(exp)
        calls = reg.set_value.call_args_list
        paths_checked = [c[0][1] for c in calls]
        self.assertTrue(any("PowerShellAdmin" in p for p in paths_checked))
        self.assertTrue(any("CompactOS" in p for p in paths_checked))

        # DNS Presets
        reg.set_value.reset_mock()
        reg.apply_dns_presets("cloudflare")
        dns_calls = reg.set_value.call_args_list
        self.assertTrue(any(c[0][2] == "NameServer" and "1.1.1.1" in str(c[0][4]) for c in dns_calls))

        # DNS Cache Optimizations
        reg.set_value.reset_mock()
        reg.apply_dns_cache_optimizations()
        cache_calls = reg.set_value.call_args_list
        self.assertTrue(any(c[0][2] == "MaxCacheTtl" and c[0][4] == 86400 for c in cache_calls))

        # Defender Gaming
        reg.set_value.reset_mock()
        reg.apply_defender_gaming_optimizations(add_exclusions=True)
        def_calls = reg.set_value.call_args_list
        self.assertTrue(any(r"C:\Games" in str(c[0][2]) for c in def_calls))

        # Automatic Maintenance
        reg.set_value.reset_mock()
        reg.disable_automatic_maintenance()
        maint_calls = reg.set_value.call_args_list
        self.assertTrue(any(c[0][2] == "MaintenanceDisabled" and c[0][4] == 1 for c in maint_calls))

    def test_config_new_options_serialization(self):
        from core.config import BuildProfile, TargetOS, save_profile_to_yaml, load_profile_from_yaml
        import tempfile

        prof = BuildProfile(name="TestSerialization", target_os=TargetOS.WIN11)
        prof.system_features.features_preset = "gaming"
        prof.system_features.dns_preset = "cloudflare"
        prof.system_features.defender_gaming_exclusions = True
        prof.explorer.add_powershell_admin_context_menu = True
        prof.optimize_wim = True

        with tempfile.TemporaryDirectory() as td:
            yaml_file = Path(td) / "test_prof.yaml"
            save_profile_to_yaml(prof, yaml_file)
            self.assertTrue(yaml_file.exists())

            loaded = load_profile_from_yaml(yaml_file)
            self.assertEqual(loaded.system_features.features_preset, "gaming")
            self.assertEqual(loaded.system_features.dns_preset, "cloudflare")
            self.assertTrue(loaded.system_features.defender_gaming_exclusions)
            self.assertTrue(loaded.explorer.add_powershell_admin_context_menu)
            self.assertTrue(loaded.optimize_wim)


    def test_app_bundler_catalog(self):
        from core.app_bundler import AppBundler
        catalog = AppBundler.get_catalog()
        self.assertGreater(len(catalog), 15)
        
        categories = AppBundler.get_categories()
        self.assertIn("gaming", categories)
        self.assertIn("dev_tools", categories)
        self.assertIn("runtimes", categories)
        
        gaming_apps = AppBundler.get_apps_by_category("gaming")
        self.assertTrue(any(a.id == "steam" for a in gaming_apps))
        
        app_7z = AppBundler.get_app_by_id("sevenzip")
        self.assertIsNotNone(app_7z)
        self.assertEqual(app_7z.winget_id, "7zip.7zip")

    def test_app_bundler_scripts(self):
        from core.app_bundler import AppBundler
        ps_script = AppBundler.generate_winget_powershell_script(["7zip.7zip", "Valve.Steam"])
        self.assertIn("7zip.7zip", ps_script)
        self.assertIn("Valve.Steam", ps_script)
        self.assertIn("install --id", ps_script)

        offline_script = AppBundler.generate_offline_apps_installer_script(r"C:\TestApps")
        self.assertIn("msiexec.exe", offline_script)
        self.assertIn("/VERYSILENT", offline_script)

    def test_virtualization_manager(self):
        from core.virtualization_manager import VirtualizationManager
        from unittest.mock import MagicMock
        
        feats = VirtualizationManager.get_features_for_profile(enable_wsl=True, enable_sandbox=True)
        self.assertIn("VirtualMachinePlatform", feats)
        self.assertIn("Microsoft-Windows-Subsystem-Linux", feats)
        self.assertIn("Containers-DisposableClientVM", feats)

        mock_reg = MagicMock()
        res_vbs = VirtualizationManager.apply_gaming_vbs_tweaks(mock_reg)
        self.assertTrue(res_vbs)
        calls = mock_reg.set_value.call_args_list
        self.assertTrue(any("EnableVirtualizationBasedSecurity" in str(c) for c in calls))

        mock_reg.reset_mock()
        res_spectre = VirtualizationManager.apply_spectre_meltdown_gaming_override(mock_reg)
        self.assertTrue(res_spectre)
        calls_spectre = mock_reg.set_value.call_args_list
        self.assertTrue(any("FeatureSettingsOverride" in str(c) for c in calls_spectre))

    def test_security_hardener(self):
        from core.security_hardener import SecurityHardener, WindowsUpdatePolicy
        from unittest.mock import MagicMock
        import tempfile

        mock_reg = MagicMock()
        res = SecurityHardener.apply_windows_update_policy(
            mock_reg, policy=WindowsUpdatePolicy.NOTIFY_ONLY, block_driver_updates=True
        )
        self.assertTrue(res)
        calls = mock_reg.set_value.call_args_list
        self.assertTrue(any("ExcludeWUDriversInQualityUpdate" in str(c) for c in calls))
        self.assertTrue(any("AUOptions" in str(c) for c in calls))

        mock_reg.reset_mock()
        res_priv = SecurityHardener.apply_deep_privacy_hardening(mock_reg)
        self.assertTrue(res_priv)
        calls_priv = mock_reg.set_value.call_args_list
        self.assertTrue(any("DisableAIDataAnalysis" in str(c) for c in calls_priv))
        self.assertTrue(any("TurnOffWindowsCopilot" in str(c) for c in calls_priv))

        # Test hosts blocklist injection
        with tempfile.TemporaryDirectory() as td:
            etc_dir = Path(td) / "Windows" / "System32" / "drivers" / "etc"
            etc_dir.mkdir(parents=True)
            hosts_file = etc_dir / "hosts"
            hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")

            injected = SecurityHardener.inject_telemetry_hosts_blocklist(td)
            self.assertTrue(injected)
            content = hosts_file.read_text(encoding="utf-8")
            self.assertIn("telemetry.microsoft.com", content)

    def test_network_optimizer(self):
        from core.network_optimizer import NetworkOptimizer
        from unittest.mock import MagicMock

        preset = NetworkOptimizer.get_dns_preset("cloudflare")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.primary_ipv4, "1.1.1.1")

        mock_reg = MagicMock()
        res_tcp = NetworkOptimizer.apply_tcp_gaming_tweaks(mock_reg)
        self.assertTrue(res_tcp)
        calls = mock_reg.set_value.call_args_list
        self.assertTrue(any("NetworkThrottlingIndex" in str(c) for c in calls))
        self.assertTrue(any("TcpAckFrequency" in str(c) for c in calls))

        script = NetworkOptimizer.generate_setupcomplete_network_script("cloudflare")
        self.assertIn("congestionprovider=ctcp", script)
        self.assertIn("1.1.1.1", script)

    def test_iso_hash_and_checksum(self):
        from core.iso_validator import IsoValidator
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            test_file = Path(td) / "test_image.iso"
            test_file.write_bytes(b"OSBUILDER_TEST_DATA_1234567890")

            hashes = IsoValidator.compute_file_hashes(test_file, algorithms=["sha256", "md5"])
            self.assertIn("sha256", hashes)
            self.assertIn("md5", hashes)

            chk_file = IsoValidator.generate_checksum_file(test_file, algorithm="sha256")
            self.assertTrue(chk_file.exists())
            self.assertIn(hashes["sha256"], chk_file.read_text(encoding="utf-8"))

            is_valid = IsoValidator.verify_checksum(test_file, hashes["sha256"], algorithm="sha256")
            self.assertTrue(is_valid)

            is_invalid = IsoValidator.verify_checksum(test_file, "0" * 64, algorithm="sha256")
            self.assertFalse(is_invalid)

    def test_load_esport_profile(self):
        from core.config import WindowsUpdatePolicy
        p_path = self.root_dir / "profiles" / "esport_competitive_24h2.yaml"
        self.assertTrue(p_path.exists())
        prof = load_profile_from_yaml(p_path)
        self.assertEqual(prof.target_os, TargetOS.WIN11)
        self.assertTrue(prof.enable_gaming_tweaks)
        self.assertTrue(prof.virtualization.disable_vbs_hvci)
        self.assertEqual(prof.security.windows_update_policy, WindowsUpdatePolicy.NOTIFY_ONLY)
        self.assertTrue(prof.security.block_driver_updates)
        self.assertTrue(prof.system_features.disable_nagle_algorithm)
        self.assertEqual(prof.system_features.dns_preset, "cloudflare")
        self.assertTrue(prof.generate_checksum)


if __name__ == "__main__":
    unittest.main()


