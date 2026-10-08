"""Regressão do smoke de implantação: nunca modificar registros reais."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "linux" / "test.sh"
FAKE_CURL = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
with open(os.environ["FAKE_CURL_LOG"], "a", encoding="utf-8") as out:
    out.write(json.dumps(args) + "\n")
if any(
    flag in args
    for flag in ("-X", "--request", "--data", "--data-binary", "-d", "-F", "--form", "-T", "--upload-file")
):
    Path(os.environ["FAKE_MUTATION_FLAG"]).write_text("mutation attempted", encoding="utf-8")
    sys.exit(93)
urls = [a for a in args if a.startswith("http://") or a.startswith("https://")]
if len(urls) != 1:
    sys.exit(92)
url = urls[0]
if "-w" in args:
    sys.stdout.write("200")
elif url.endswith("/api/health"):
    print(json.dumps({"status": os.environ.get("FAKE_HEALTH_STATUS", "ok")}))
elif url.endswith("/api/etapas"):
    print(json.dumps([{"etapa": str(i)} for i in range(6)]))
elif url.endswith("/api/propostas/stats"):
    print('{"total_propostas":1}')
elif "uf=BA" in url:
    print('{"total":1}')
elif "/api/propostas?por_pagina=" in url:
    print('{"items":[{"num_proposta":"synthetic-001"}],"total":1}')
elif url.endswith("/api/propostas/synthetic-001"):
    print('{"num_proposta":"synthetic-001","historico":[]}')
elif url.endswith("/"):
    print('<html><head><title>MCMV Rural</title></head><body><script src="/assets/app.js"></script></body></html>')
else:
    sys.exit(91)
'''


class ReadonlySmokeTests(unittest.TestCase):
    def run_smoke(self, *, health: str = "ok") -> tuple[subprocess.CompletedProcess[str], list[list[str]], bool]:
        with tempfile.TemporaryDirectory(prefix="mcmv-readonly-smoke-") as folder:
            tmp = Path(folder)
            mock = tmp / "curl"
            mock.write_text(FAKE_CURL, encoding="utf-8")
            mock.chmod(0o755)
            logfile = tmp / "curl.jsonl"
            mutation_file = tmp / "mutation.flag"
            env = {
                **os.environ,
                "PATH": f"{tmp}:{os.environ.get('PATH', '')}",
                "FAKE_CURL_LOG": str(logfile),
                "FAKE_MUTATION_FLAG": str(mutation_file),
                "FAKE_HEALTH_STATUS": health,
            }
            result = subprocess.run(
                ["bash", str(SCRIPT), "--local"],
                env=env,
                cwd=SCRIPT.parents[2],
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
            requests = [
                json.loads(line)
                for line in logfile.read_text(encoding="utf-8").splitlines()
            ] if logfile.exists() else []
            return result, requests, mutation_file.exists()

    def test_smoke_read_only_and_real_details(self) -> None:
        result, requests, attempted_write = self.run_smoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(attempted_write)
        self.assertGreaterEqual(len(requests), 8)
        self.assertTrue(any("/api/propostas/synthetic-001" in " ".join(req) for req in requests))
        self.assertTrue(all(" -X " not in f" {' '.join(req)} " for req in requests))
        self.assertTrue(all("-k" not in req and "-sk" not in req for req in requests))
        self.assertIn("read-only", result.stdout)
        self.assertIn("PUT", result.stdout)
        self.assertIn("Todos os testes passaram", result.stdout)

    def test_reject_semantic_false_success(self) -> None:
        result, requests, attempted_write = self.run_smoke(health="erro")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stdout)
        self.assertFalse(attempted_write)
        self.assertGreaterEqual(len(requests), 8)

    def test_static_gate_blocks_mutations(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("-X PUT", script)
        self.assertNotIn("--data-binary", script)
        self.assertNotIn("curl -sk", script)
        self.assertNotIn("Revertido pelo teste", script)


if __name__ == "__main__":
    unittest.main()
