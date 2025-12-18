#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
▄▄▄█████▓ ██▀███   █    ██  ▄▄▄█████▓ ██░ ██ 
▓  ██▒ ▓▒▓██ ▒ ██▒ ██  ▓██▒ ▓  ██▒ ▓▒▓██░ ██▒
▒ ▓██░ ▒░▓██ ░▄█ ▒▓██  ▒██░ ▒ ▓██░ ▒░▒██▀▀██░
░ ▓██▓ ░ ▒██▀▀█▄  ▓▓█  ░██░ ░ ▓██▓ ░ ░▓█ ░██ 
  ▒██▒ ░ ░██▓ ▒██▒▒▒█████▓    ▒██▒ ░ ░▓█▒░██▓
  ▒ ░░   ░ ▒▓ ░▒▓░░▒▓▒ ▒ ▒    ▒ ░░    ▒ ░░▒░▒
    ░      ░▒ ░ ▒░░░▒░ ░ ░      ░     ▒ ░▒░ ░
  ░        ░░   ░  ░░░ ░ ░    ░       ░  ░░ ░
            ░        ░                ░  ░   

Project: CTF Image Resurrector v3.0
Author: Hackerchen716
Features: Multi-threaded CRC32 Cracking | Hex Visualization | Zero-Dependency
License: MIT
"""

import zlib
import struct
import argparse
import sys
import time
import concurrent.futures
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List

# --- 1. Cyberpunk UI Engine (Zero-Dependency) ---
class Term:
    """Terminal control sequences for that hacker aesthetic."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Neon Colors
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    
    # Icons
    ICON_ROCKET = "🚀"
    ICON_GEAR = "⚙️ "
    ICON_CHECK = "✅"
    ICON_skull = "💀"
    ICON_LOCK = "🔒"
    ICON_KEY = "🔑"

    @staticmethod
    def banner():
        print(f"{Term.CYAN}{Term.BOLD}")
        print(r"""
    ██▓███   ██▀███   ▒█████   ▄▄▄█████▓  ▒█████   ▄████▄   ▒█████   ██▓
   ▓██░  ██▒▓██ ▒ ██▒▒██▒  ██▒ ▓  ██▒ ▓▒ ▒██▒  ██▒▒██▀ ▀█  ▒██▒  ██▒▓██▒
   ▓██░ ██▓▒▓██ ░▄█ ▒▒██░  ██▒ ▒ ▓██░ ▒░ ▒██░  ██▒▒▓█    ▄ ▒██░  ██▒▒██▒
   ▒██▄█▓▒ ▒▒██▀▀█▄  ▒██   ██░ ░ ▓██▓ ░  ▒██   ██░▒▓▓▄ ▄██▒▒██   ██░░██░
   ▒██▒ ░  ░░██▓ ▒██▒░ ████▓▒░   ▒██▒ ░  ░ ████▓▒░▒ ▓███▀ ░░ ████▓▒░░██░
   ▒▓▒░ ░  ░░ ▒▓ ░▒▓░░ ▒░▒░▒░    ▒ ░░    ░ ▒░▒░▒░ ░ ░▒ ▒  ░░ ▒░▒░▒░ ░▓  
   ░▒ ░       ░▒ ░ ▒░  ░ ▒ ▒░      ░       ░ ▒ ▒░   ░  ▒     ░ ▒ ▒░  ▒ ░
   ░░         ░░   ░ ░ ░ ░ ▒     ░       ░ ░ ░ ▒  ░        ░ ░ ░ ▒   ▒ ░
               ░         ░ ░                 ░ ░  ░ ░          ░ ░   ░  
                                                  ░                     
        """)
        print(f"   >>> SYSTEM ONLINE: {Term.GREEN}CTF Image Resurrector v3.0{Term.CYAN} <<<")
        print(f"   >>> MODE: {Term.MAGENTA}Advanced Heuristics & Multi-threading{Term.CYAN} <<<{Term.RESET}\n")

    @staticmethod
    def print_hex_diff(offset: int, old_bytes: bytes, new_bytes: bytes):
        """Visualizes the byte patch in a hex-editor style."""
        print(f"\n{Term.DIM}   [HEX DUMP VIEW] @ Offset 0x{offset:X}{Term.RESET}")
        print(f"   {Term.RED}OLD: {' '.join(f'{b:02X}' for b in old_bytes)}  <-- Corrupted{Term.RESET}")
        print(f"   {Term.GREEN}NEW: {' '.join(f'{b:02X}' for b in new_bytes)}  <-- Patched{Term.RESET}\n")

    @staticmethod
    def log(msg: str, level="INFO"):
        if level == "INFO":
            print(f"{Term.BLUE}[*]{Term.RESET} {msg}")
        elif level == "SUCCESS":
            print(f"{Term.GREEN}[+]{Term.RESET} {msg}")
        elif level == "WARN":
            print(f"{Term.YELLOW}[!]{Term.RESET} {msg}")
        elif level == "ERROR":
            print(f"{Term.RED}[-]{Term.RESET} {msg}")


# --- 2. Core Logic (The Brain) ---

@dataclass
class ImageMeta:
    width: int
    height: int
    format: str

class ImageFixer:
    def __init__(self, path: Path):
        self.path = path
        try:
            with open(path, 'rb') as f:
                self.data = bytearray(f.read())
        except FileNotFoundError:
            Term.log(f"Target lost: {path}", "ERROR")
            sys.exit(1)

    def identify(self) -> str:
        if self.data.startswith(b'\x89\x50\x4E\x47\r\n\x1a\n'):
            return "PNG"
        elif self.data.startswith(b'\xFF\xD8'):
            return "JPG"
        return "UNKNOWN"

    def save(self, suffix="_fixed"):
        out_path = self.path.with_name(f"{self.path.stem}{suffix}{self.path.suffix}")
        with open(out_path, 'wb') as f:
            f.write(self.data)
        Term.log(f"Artifact secured: {Term.BOLD}{out_path}{Term.RESET}", "SUCCESS")

    def fix_jpg(self):
        Term.log("Initiating JPG Heuristic Scan...", "INFO")
        # Find SOF0 (Baseline) or SOF2 (Progressive)
        markers = {b'\xFF\xC0': 'SOF0', b'\xFF\xC2': 'SOF2'}
        
        found = False
        for m, name in markers.items():
            idx = self.data.find(m)
            if idx != -1:
                found = True
                Term.log(f"Marker identified: {Term.YELLOW}{name}{Term.RESET} at 0x{idx:X}")
                
                # Format: [Marker 2] [Len 2] [Precision 1] [Height 2] [Width 2]
                h_offset = idx + 5
                w_offset = idx + 7
                
                old_h_bytes = self.data[h_offset:h_offset+2]
                cur_h = struct.unpack('>H', old_h_bytes)[0]
                cur_w = struct.unpack('>H', self.data[w_offset:w_offset+2])[0]
                
                Term.log(f"Current Geometry: {cur_w}x{cur_h}", "INFO")
                
                # Intelligence: Usually height should match width or be larger in these CTF puzzles
                new_h = max(cur_w, cur_h + 1000) 
                # Cap at 65535
                new_h = min(new_h, 65535)
                
                new_h_bytes = struct.pack('>H', new_h)
                
                Term.print_hex_diff(h_offset, old_h_bytes, new_h_bytes)
                
                self.data[h_offset:h_offset+2] = new_h_bytes
                Term.log(f"Height brute-forced to: {new_h}", "SUCCESS")
                break
        
        if not found:
            Term.log("No structural anomalies detected or unknown JPG format.", "WARN")
            return False
        return True

    def _crack_png_chunk(self, args) -> Optional[int]:
        """Worker function for multi-threading."""
        start_h, end_h, fixed_chunk_prefix, fixed_chunk_suffix, target_crc = args
        
        for h in range(start_h, end_h):
            # Construct candidate chunk
            new_h_bytes = struct.pack('>I', h)
            data = fixed_chunk_prefix + new_h_bytes + fixed_chunk_suffix
            
            if (zlib.crc32(data) & 0xffffffff) == target_crc:
                return h
        return None

    def fix_png(self):
        Term.log("Analyzing IHDR integrity...", "INFO")
        
        # PNG IHDR Layout:
        # [Length 4] [ChunkType 4] [Width 4] [Height 4] [Depth 1] ... [CRC 4]
        # CRC is calculated over ChunkType + Data
        
        try:
            IHDR_START = 12
            WIDTH_OFFSET = 16
            HEIGHT_OFFSET = 20
            CRC_OFFSET = 29
            
            current_w = struct.unpack('>I', self.data[WIDTH_OFFSET:WIDTH_OFFSET+4])[0]
            current_h = struct.unpack('>I', self.data[HEIGHT_OFFSET:HEIGHT_OFFSET+4])[0]
            target_crc = struct.unpack('>I', self.data[CRC_OFFSET:CRC_OFFSET+4])[0]
            
            Term.log(f"Reported Geometry: {current_w}x{current_h} | CRC32: {hex(target_crc)}", "INFO")
            Term.log(f"{Term.ICON_LOCK} CRC Mismatch detected. Engaging multi-threaded brute-force...", "WARN")

            # Prepare data for workers
            # We only vary the 4 bytes of height.
            # Prefix: Type(4) + Width(4)
            chunk_prefix = self.data[IHDR_START:HEIGHT_OFFSET]
            # Suffix: BitDepth(1) + ColorType(1) + Comp(1) + Filter(1) + Interlace(1)
            chunk_suffix = self.data[HEIGHT_OFFSET+4:CRC_OFFSET]

            # Define search space (Current Height -> 10000 pixels more)
            # Split into chunks for threads
            MAX_SEARCH = 10000
            THREAD_COUNT = 8
            step = MAX_SEARCH // THREAD_COUNT
            
            tasks = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                for i in range(THREAD_COUNT):
                    start = current_h + (i * step)
                    end = start + step
                    tasks.append(executor.submit(
                        self._crack_png_chunk, 
                        (start, end, chunk_prefix, chunk_suffix, target_crc)
                    ))
                
                print(f"   {Term.DIM}>>> Spawning {THREAD_COUNT} hunter threads...{Term.RESET}")
                
                found_h = None
                for future in concurrent.futures.as_completed(tasks):
                    result = future.result()
                    if result:
                        found_h = result
                        # Cancel other threads (best effort)
                        break
            
            if found_h:
                Term.log(f"{Term.ICON_KEY} MATCH FOUND! Real Height: {found_h}", "SUCCESS")
                
                old_bytes = struct.pack('>I', current_h)
                new_bytes = struct.pack('>I', found_h)
                Term.print_hex_diff(HEIGHT_OFFSET, old_bytes, new_bytes)
                
                self.data[HEIGHT_OFFSET:HEIGHT_OFFSET+4] = new_bytes
                return True
            else:
                Term.log("Exhausted search space. Width might also be corrupted.", "ERROR")
                return False

        except Exception as e:
            Term.log(f"Critical Failure: {e}", "ERROR")
            return False

# --- 3. Entry Point ---

def main():
    Term.banner()
    parser = argparse.ArgumentParser(description="CTF Image Height Restoration Tool")
    parser.add_argument("file", help="Path to the corrupted image")
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    path = Path(args.file)

    if not path.exists():
        Term.log("Target file does not exist.", "ERROR")
        sys.exit(1)

    fixer = ImageFixer(path)
    fmt = fixer.identify()
    
    Term.log(f"Target Identified: {Term.BOLD}{fmt}{Term.RESET} Format", "INFO")
    
    start_time = time.time()
    success = False
    
    if fmt == "PNG":
        success = fixer.fix_png()
    elif fmt == "JPG":
        success = fixer.fix_jpg()
    else:
        Term.log("Unsupported format or invalid header signature.", "ERROR")

    if success:
        fixer.save()
        elapsed = time.time() - start_time
        print(f"\n{Term.GREEN}{Term.BOLD}MISSION ACCOMPLISHED in {elapsed:.4f}s{Term.RESET}")
        print(f"{Term.DIM}Keep hacking, stay safe.{Term.RESET}")
    else:
        print(f"\n{Term.RED}MISSION FAILED.{Term.RESET}")

if __name__ == "__main__":
    main()