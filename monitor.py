#!/usr/bin/env python3
"""NIBIRU telemetry monitor: mesh registry, metrics log, and cat/sed/awk utilities.
Run as a daemon next to server.js. Pass --demo for the 5 second walkthrough."""
import argparse
import json
import logging
import os
import random
import re
import signal
import threading
from datetime import datetime, timezone
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nibiru.monitor")
DATA_DIR = os.environ.get("NIBIRU_DATA_DIR", "data")
MAX_LOG_BYTES = 5 * 1024 * 1024


class ThreadedMonitorRegistry:
    def __init__(self, data_dir: str = DATA_DIR):
        os.makedirs(data_dir, exist_ok=True)
        self.state_file = os.path.join(data_dir, "circuit_state_matrix.json")
        self.report_file = os.path.join(data_dir, "circuit_metrics.log")
        self.members_file = os.path.join(data_dir, "registry.public.json")
        self.root_registry: Dict[str, dict] = {}
        self.mesh_links: List[List[str]] = []
        self.lock = threading.RLock()
        self.is_monitoring = False
        self._stop = threading.Event()
        self._monitor_thread = None

    # ---- registry ----
    def deploy_new_root(self, root_id: str, label: str, role: str):
        with self.lock:
            self.root_registry[root_id] = {"label": label, "role": role,
                                           "deployed": datetime.now(timezone.utc).isoformat()}
        logger.info("ROOT DEPLOYED: %s (%s)", root_id, label)

    def add_mesh_link(self, a: str, b: str) -> bool:
        with self.lock:
            if a not in self.root_registry or b not in self.root_registry:
                logger.error("LINK REJECTED: unknown root in %s <-> %s", a, b)
                return False
            self.mesh_links.append([a, b])
        return True

    def member_count(self) -> int:
        try:
            with open(self.members_file, encoding="utf-8") as f:
                return len([m for m in json.load(f) if m.get("status") == "active"])
        except (IOError, ValueError):
            return 0

    def export_state_matrix(self) -> bool:
        with self.lock:
            snapshot = {"roots": self.root_registry, "links": self.mesh_links}
            tmp = self.state_file + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, indent=4)
                os.replace(tmp, self.state_file)
                return True
            except IOError as err:
                logger.error("FILE SYSTEM ACCESS FAILURE: %s", err)
                return False

    def append_telemetry_metric(self, node_count: int, amplitude: float):
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self.lock:
            try:
                if os.path.exists(self.report_file) and os.path.getsize(self.report_file) > MAX_LOG_BYTES:
                    os.replace(self.report_file, self.report_file + ".1")
                with open(self.report_file, "a", encoding="utf-8") as f:
                    f.write(f"{ts} METRIC nodes:{node_count} amp:{amplitude:.4f}_uV "
                            f"members:{self.member_count()} status:ACTIVE\n")
            except IOError as err:
                logger.error("METRICS FILE APPEND FAILURE: %s", err)

    # ---- cat / sed / awk equivalents ----
    def execute_cat_stream(self, filepath: str) -> List[str]:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().splitlines()
        except IOError:
            return []

    def execute_sed_replace(self, filepath: str, pattern: str, replacement: str):
        lines = self.execute_cat_stream(filepath)
        if not lines:
            return
        rx = re.compile(pattern)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(rx.sub(replacement, ln) for ln in lines) + "\n")
        except IOError as err:
            logger.error("SED INLINE MODIFICATION FAULT: %s", err)

    def execute_awk_filter(self, filepath: str, threshold: float = 10.0) -> List[str]:
        out = []
        for line in self.execute_cat_stream(filepath):
            fields = line.split()
            if len(fields) < 5:
                continue
            try:
                amp = float(fields[3].replace("amp:", "").replace("_uV", ""))
            except ValueError:
                continue
            if amp > threshold:
                out.append(f"[AWK Match] Time: {fields[0]} | Components: {fields[2]} | Signal: {fields[3]}")
        return out

    # ---- daemon ----
    def start_background_telemetry_loop(self, check_interval: float = 1.0):
        if self.is_monitoring:
            logger.warning("Telemetry loop daemon already processing cycles.")
            return
        self.is_monitoring = True
        self._stop.clear()
        self._monitor_thread = threading.Thread(target=self._telemetry_worker, args=(check_interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("BACKGROUND DAEMON ACTIVATED")

    def stop_background_telemetry_loop(self):
        self.is_monitoring = False
        self._stop.set()
        if self._monitor_thread:
            self._monitor_thread.join()
        logger.info("BACKGROUND DAEMON DEACTIVATED")

    def _telemetry_worker(self, interval: float):
        while not self._stop.is_set():
            with self.lock:
                nodes = len(self.root_registry)
            self.append_telemetry_metric(nodes, random.uniform(8.5, 12.2))  # simulated signal
            self.export_state_matrix()
            self._stop.wait(interval)


def build_default_mesh() -> ThreadedMonitorRegistry:
    mesh = ThreadedMonitorRegistry()
    mesh.deploy_new_root("ROOT-N200", "Primary Spine Core", "Throughput Substrate")
    mesh.deploy_new_root("ROOT-P300", "Avatar 3D Head-Shadow Mesh", "Resource Controller")
    mesh.deploy_new_root("ROOT-A3PS", "a3pState Conversion Vault", "Inventory Anchor")
    mesh.add_mesh_link("ROOT-N200", "ROOT-P300")
    return mesh


def run_daemon():
    mesh = build_default_mesh()
    mesh.start_background_telemetry_loop(5.0)
    done = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: done.set())
    done.wait()
    mesh.stop_background_telemetry_loop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    run_daemon()
