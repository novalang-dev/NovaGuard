# -*- coding: utf-8 -*-
"""Katman 1: SHA-256 imza taraması."""
import os
from core.database import SignatureDB, sha256_of_file
from core.config import CHUNK_SIZE


class SignatureScanner:
    def __init__(self):
        self.db = SignatureDB()

    def scan_file(self, path):
        try:
            if not os.path.isfile(path):
                return (False, None, 0, None)
            sha = sha256_of_file(path, CHUNK_SIZE)
            hit = self.db.lookup(sha)
            if hit:
                return (True, hit[0], hit[1], sha)
            return (False, None, 0, sha)
        except Exception:
            return (False, None, 0, None)

    def scan_directory(self, root, progress_cb=None):
        findings = []
        files = []
        try:
            for r, _, fs in os.walk(root):
                for f in fs:
                    files.append(os.path.join(r, f))
        except Exception as e:
            print(f"[L1] walk: {e}")
            return findings
        total = len(files)
        for i, fp in enumerate(files, 1):
            t, name, lvl, sha = self.scan_file(fp)
            if t:
                findings.append({"path": fp, "name": name, "level": lvl,
                                 "sha256": sha, "layer": 1})
            if progress_cb and i % 25 == 0:
                progress_cb(i, total)
        if progress_cb:
            progress_cb(total, total)
        return findings