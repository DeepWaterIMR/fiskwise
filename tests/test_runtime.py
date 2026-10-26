"""Offline unit tests for runtime discovery and stable-line selection."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import unittest.mock
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_runtime.py"
SPEC = importlib.util.spec_from_file_location("fiskwise_check_runtime", SCRIPT)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class StableReleaseTests(unittest.TestCase):
    def test_returns_newest_two_distinct_stable_lines(self):
        self.assertEqual(runtime.stable_lines([
            "4.4.3", "4.5.0", "4.5.2", "4.6.0-rc1", "4.6.0", "3.6.9", "bad"
        ]), ["4.6", "4.5"])

    def test_cran_index_extracts_release_lines(self):
        index = '<a href="R-4/">R-4</a><a href="R-3/">R-3</a>'
        self.assertEqual(runtime.r_major_directories(index), ["R-4/", "R-3/"])
        pages = ['<a href="R-4.6.1.tar.gz">new</a><a href="R-4.5.3.tar.gz">old</a>',
                 '<a href="R-3.6.3.tar.gz">older</a>']
        self.assertEqual(runtime.r_versions_from_pages(pages), ["4.6.1", "4.5.3", "3.6.3"])
        self.assertIsNone(runtime.r_major_directories(None))

    def test_official_r_discovery_fetches_found_major_directories(self):
        pages = {
            runtime.CRAN_R_INDEX: '<a href="R-4/">R-4</a><a href="R-3/">R-3</a>',
            runtime.CRAN_R_INDEX + "R-4/": '<a href="R-4.6.1.tar.gz">R</a>',
            runtime.CRAN_R_INDEX + "R-3/": '<a href="R-3.6.3.tar.gz">R</a>',
        }
        self.assertEqual(runtime.official_r_versions(lambda url: pages.get(url)), ["4.6.1", "3.6.3"])

    def test_fetch_retries_slow_handshake_before_reporting_unknown(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"R-4.6.1.tar.gz"
        with patch.object(runtime.urllib.request, "urlopen",
                          side_effect=[TimeoutError("handshake timed out"), response]) as urlopen:
            self.assertEqual(runtime.fetch_text(runtime.CRAN_R_INDEX), "R-4.6.1.tar.gz")
        self.assertEqual(urlopen.call_count, 2)
        self.assertGreaterEqual(urlopen.call_args.kwargs["timeout"], 20)
        with patch.object(runtime.urllib.request, "urlopen", side_effect=TimeoutError("offline")):
            self.assertIsNone(runtime.fetch_text(runtime.CRAN_R_INDEX))

    def test_quarto_metadata_excludes_prerelease_and_keeps_full_version(self):
        releases = json.dumps([
            {"tag_name": "v1.7.0", "draft": False, "prerelease": False},
            {"tag_name": "v1.8.0-rc1", "draft": False, "prerelease": True},
            {"tag_name": "v1.6.2", "draft": False, "prerelease": False},
        ])
        self.assertEqual(runtime.quarto_stable_versions(releases), ["v1.7.0", "v1.6.2"])
        self.assertEqual(runtime.stable_lines(runtime.quarto_stable_versions(releases)), ["1.7", "1.6"])
        self.assertIsNone(runtime.quarto_stable_versions("offline"))

    def test_release_action_identifies_old_lines_and_updates(self):
        versions = ["4.6.1", "4.5.3", "4.4.3"]
        self.assertEqual(runtime.release_action("4.6.0", versions), "update to 4.6.1")
        self.assertIn("supported older stable line", runtime.release_action("4.5.0", versions))
        self.assertIn("outside newest two", runtime.release_action("4.4.3", versions))

    def test_selected_development_and_newer_versions_are_preserved(self):
        versions = ["4.6.1", "4.5.3"]
        for selected in ["4.7.0-dev", "4.7.0-rc1", "R Under development (unstable)"]:
            self.assertIn("preserve", runtime.release_action(selected, versions))
            self.assertNotIn("upgrade", runtime.release_action(selected, versions))
        self.assertIn("preserve", runtime.release_action("4.7.0", versions))

    def test_offline_inspection_marks_remote_data_unknown(self):
        with patch.object(runtime, "run_version", return_value=None), \
             patch.object(runtime, "user_library", return_value={"configured": None, "existing": None, "writable": False}):
            result = runtime.inspect(offline=True)
        self.assertEqual(result["R"]["latest_stable_lines"], "unknown")
        self.assertEqual(result["quarto_cli"]["latest_stable_lines"], "unknown")
        self.assertEqual(result["quarto_cli"]["version"], "unknown")


class RPackageManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rscript = shutil.which("Rscript")
        if cls.rscript and subprocess.run([cls.rscript, "-e", "quit(status=!requireNamespace('jsonlite', quietly=TRUE))"],
                                          capture_output=True).returncode != 0:
            cls.rscript = None

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is unavailable")
    def test_sourceable_inventory_and_consent_functions_without_installing(self):
        if not self.rscript:
            self.skipTest("jsonlite is unavailable")
        expression = (
            f'source({json.dumps(str(Path(__file__).resolve().parents[1] / "scripts" / "manage_r_packages.R"))}); '
            f'inv <- jsonlite::fromJSON({json.dumps(str(Path(__file__).resolve().parents[1] / "packages.json"))}, simplifyVector=FALSE); '
            'pkgs <- managed_packages(inv, list(components=list(fiskwise=list(), BAIT=list()))); '
            'stopifnot(all(c("DBI", "tidyverse", "ggOceanMaps", "ggFishPlots") %in% names(pkgs))); '
            'stopifnot(installation_permitted(TRUE, TRUE, "", FALSE, tempdir())); '
            'stopifnot(!installation_permitted(FALSE, TRUE, "", FALSE, tempdir())); '
            'stopifnot(!installation_permitted(TRUE, TRUE, "false", FALSE, tempdir())); '
            'stopifnot(!installation_permitted(TRUE, TRUE, "", TRUE, tempdir())); '
            'stopifnot(!installation_permitted(TRUE, FALSE, "", FALSE, tempdir())); '
            'stopifnot(is.null(installed_package("fiskwiseNoSuchPackage"))); '
            'stopifnot(is.null(installed_description("fiskwiseNoSuchPackage"))); '
            'stopifnot(identical(unname(cran_repo_options(c(CRAN="@CRAN@"))), "https://cloud.r-project.org")); '
            'idx <- matrix("", nrow=4, ncol=6, dimnames=list(c("foo", "bar", "ghdep", "suggested"), c("Package", "Version", "Depends", "Imports", "LinkingTo", "Suggests"))); '
            'idx["foo", "Version"] <- "2.0.0"; idx["foo", "Imports"] <- "bar (>= 1.0)"; '
            'idx["foo", "Suggests"] <- "suggested"; '
            'stopifnot(identical(package_dependencies(idx, "foo"), "bar")); '
            'stopifnot(package_status(list(name="foo", source="CRAN"), list(version="1.0.0"), idx)$state == "outdated"); '
            'mock_sha <- function(source, ref) "abc123"; '
            'gh <- package_status(list(name="foo", source="owner/repo", ref="main"), list(version="1", remote_sha="abc123"), idx, mock_sha); '
            'stopifnot(gh$state == "current"); '
            'pin <- package_status(list(name="foo", source="owner/repo", ref="preserve-installed"), list(version="1", remote_ref="custom"), idx, mock_sha); '
            'stopifnot(pin$state == "custom pin preserved"); '
            'custom <- package_status(list(name="foo", source="owner/repo", ref="default"), list(version="1", remote_ref="feature/pinned", remote_sha="xyz"), idx, mock_sha); '
            'stopifnot(custom$state == "custom pin preserved"); '
            'pkg <- list(name="foo", source="owner/repo", ref="default"); '
            'installed <- list(version="1", remote_ref="abc123", remote_sha="abc123"); '
            'recorded <- c(installed, list(source="owner/repo", requested_ref="default")); '
            'owned <- managed_installed(pkg, installed, recorded); '
            'stopifnot(package_status(pkg, owned, idx, mock_sha)$state == "current"); '
            'stopifnot(package_status(pkg, managed_installed(pkg, installed, NULL), idx, mock_sha)$preserve); '
            'installed$remote_ref <- "custom-branch"; '
            'stopifnot(package_status(pkg, managed_installed(pkg, installed, recorded), idx, mock_sha)$preserve); '
            'installed$remote_ref <- "abc123"; installed$remote_sha <- "other"; '
            'stopifnot(package_status(pkg, managed_installed(pkg, installed, recorded), idx, mock_sha)$preserve); '
            'sha_calls <- 0L; cached_sha <- memoize_github_sha(function(source, ref) { sha_calls <<- sha_calls + 1L; "abc123" }); '
            'cached_sha("owner/repo", "HEAD"); cached_sha("owner/repo", "HEAD"); stopifnot(sha_calls == 1L); '
            'mock_description <- function(source, sha, subdir=NULL) { '
            'if (source == "owner/root") return(paste(c("Package: root", "Imports: bar, ghdep", "Suggests: suggested", "Remotes: ghdep=other/ghdep@v1"), collapse="\\n")); '
            'if (source == "other/ghdep") return(paste(c("Package: ghdep", "Imports: bar"), collapse="\\n")); NULL }; '
            'expanded <- expand_github_packages(list(root=list(name="root", source="owner/root", ref="default", subdir="Rpkg")), idx, '
            'sha_lookup=cached_sha, description_lookup=mock_description, installed_lookup=function(name) NULL, '
            'installed_description_lookup=function(name) NULL, base_packages=character()); '
            'stopifnot(all(c("root", "bar", "ghdep") %in% names(expanded$packages))); '
            'stopifnot(!"suggested" %in% names(expanded$packages), length(expanded$unknown) == 0L); '
            'stopifnot(github_description_url("owner/root", "abc1234", "Rpkg") == "https://raw.githubusercontent.com/owner/root/abc1234/Rpkg/DESCRIPTION"); '
            'unknown <- expand_github_packages(list(root=list(name="root", source="owner/root", ref="default")), idx, '
            'sha_lookup=function(source, ref) NA_character_, description_lookup=function(...) NULL, '
            'installed_lookup=function(name) NULL, installed_description_lookup=function(name) NULL, base_packages=character()); '
            'stopifnot(length(unknown$unknown) > 0L); '
            'stale <- expand_github_packages(list(root=list(name="root", source="owner/root", ref="default")), idx, '
            'sha_lookup=function(source, ref) "abc123", description_lookup=function(...) NULL, '
            'installed_lookup=function(name) list(remote_sha="oldsha"), '
            'installed_description_lookup=function(name) list(Imports="bar"), base_packages=character()); '
            'stopifnot(any(grepl("not for checked GitHub SHA", stale$unknown))); '
            'stopifnot(!installation_permitted(TRUE, TRUE, "", FALSE, tempdir(), dependencies_known=FALSE)); '
            'cat("R package manager fixture checks passed\\n")'
        )
        result = subprocess.run([self.rscript, "-e", expression], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is unavailable")
    def test_cli_dry_run_fixture_ignores_registry_root_and_apply_fails_closed(self):
        if not self.rscript:
            self.skipTest("jsonlite is unavailable")
        script = Path(__file__).resolve().parents[1] / "scripts" / "manage_r_packages.R"
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / "packages.json"
            registry = Path(directory) / "registry.json"
            inventory.write_text("[]")
            registry.write_text('{"components":{"fiskwise":{}}}')
            env = dict(__import__("os").environ, FISKWise_INVENTORY=str(inventory), FISKWise_REGISTRY=str(registry))
            dry = subprocess.run([self.rscript, str(script)], capture_output=True, text=True, env=env)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("No managed R packages", dry.stdout)
            apply = subprocess.run([self.rscript, str(script), "--apply"], capture_output=True, text=True, env=env)
            self.assertNotEqual(apply.returncode, 0)
            self.assertIn("consent.r_packages=true", apply.stderr)
            registry.write_text('{"components":{"fiskwise":{}},"consent":{"r_packages":true}}')
            env["R_AW_INSTALL_MISSING"] = "false"
            blocked = subprocess.run([self.rscript, str(script), "--apply"], capture_output=True, text=True, env=env)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("R_AW_INSTALL_MISSING=false", blocked.stderr)


if __name__ == "__main__":
    unittest.main()
