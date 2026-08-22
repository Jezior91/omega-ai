"""
OMEGA-AI :: Decoder / Encoder Module
======================================
Universal encoder/decoder for common formats and ciphers.
"""

import base64
import binascii
import json
import urllib.parse
import hashlib
import html
from typing import Any


class Decoder:
    """Universal encode/decode engine."""

    # ── Detect format ────────────────────────────────────────────────────────
    def detect(self, data: str) -> list[str]:
        candidates = []
        # Base64
        try:
            decoded = base64.b64decode(data + "==")
            decoded.decode("utf-8")
            candidates.append("base64")
        except Exception:
            pass
        # Hex
        try:
            bytes.fromhex(data.replace(" ", ""))
            candidates.append("hex")
        except Exception:
            pass
        # URL encoded
        if "%" in data:
            candidates.append("url_encoded")
        # HTML entities
        if "&" in data and ";" in data:
            candidates.append("html_entities")
        # JSON
        try:
            json.loads(data)
            candidates.append("json")
        except Exception:
            pass
        # Binary
        clean = data.replace(" ", "")
        if all(c in "01" for c in clean) and len(clean) % 8 == 0:
            candidates.append("binary")
        return candidates or ["unknown"]

    # ── Decode ───────────────────────────────────────────────────────────────
    def decode(self, data: str, format: str = "auto") -> dict:
        if format == "auto":
            candidates = self.detect(data)
            results = {}
            for fmt in candidates:
                try:
                    results[fmt] = self._decode_one(data, fmt)
                except Exception as e:
                    results[fmt] = f"[error: {e}]"
            return {"input": data, "detected": candidates, "results": results}
        try:
            return {"input": data, "format": format, "result": self._decode_one(data, format)}
        except Exception as e:
            return {"input": data, "format": format, "error": str(e)}

    def _decode_one(self, data: str, fmt: str) -> Any:
        if fmt == "base64":
            return base64.b64decode(data + "==").decode("utf-8", errors="replace")
        if fmt == "hex":
            return bytes.fromhex(data.replace(" ", "")).decode("utf-8", errors="replace")
        if fmt == "binary":
            bits = data.replace(" ", "")
            chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
            return "".join(chars)
        if fmt == "url_encoded":
            return urllib.parse.unquote(data)
        if fmt == "html_entities":
            return html.unescape(data)
        if fmt == "json":
            return json.loads(data)
        if fmt == "rot13":
            return data.translate(str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
            ))
        if fmt == "caesar":
            return "".join(chr((ord(c) - 65 - 13) % 26 + 65) if c.isupper()
                           else chr((ord(c) - 97 - 13) % 26 + 97) if c.islower()
                           else c for c in data)
        raise ValueError(f"Unknown format: {fmt}")

    # ── Encode ───────────────────────────────────────────────────────────────
    def encode(self, data: str, format: str) -> dict:
        try:
            result = self._encode_one(data, format)
            return {"input": data, "format": format, "result": result}
        except Exception as e:
            return {"input": data, "format": format, "error": str(e)}

    def _encode_one(self, data: str, fmt: str) -> str:
        if fmt == "base64":
            return base64.b64encode(data.encode()).decode()
        if fmt == "hex":
            return data.encode().hex()
        if fmt == "binary":
            return " ".join(format(b, "08b") for b in data.encode())
        if fmt == "url":
            return urllib.parse.quote(data)
        if fmt == "md5":
            return hashlib.md5(data.encode()).hexdigest()
        if fmt == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        if fmt == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        if fmt == "html":
            return html.escape(data)
        if fmt == "rot13":
            return self._decode_one(data, "rot13")
        raise ValueError(f"Unknown encode format: {fmt}")

    # ── Hash ─────────────────────────────────────────────────────────────────
    def hash_info(self, hash_str: str) -> dict:
        length = len(hash_str)
        guesses = {32: "MD5", 40: "SHA1", 56: "SHA224", 64: "SHA256",
                   96: "SHA384", 128: "SHA512"}
        return {"hash": hash_str, "length": length, "likely_type": guesses.get(length, "Unknown")}


# ── Standalone functions for omega.py ──────────────────────────────────────
_decoder_instance = Decoder()

SUPPORTED_FORMATS = [
    "base64", "hex", "binary", "url_encoded", "html_entities",
    "json", "rot13", "md5", "sha256", "sha512"
]


def decode_data(data: str, fmt: str) -> str:
    result = _decoder_instance.decode(data, fmt)
    if isinstance(result, dict) and "result" not in result:
        # auto mode returns dict of format->result mappings
        parts = []
        for k, v in result.items():
            val = v.get("result", str(v)) if isinstance(v, dict) else str(v)
            parts.append(f"[{k}]: {val}")
        return "\n".join(parts)
    return str(result.get("result", result)) if isinstance(result, dict) else str(result)


def encode_data(data: str, fmt: str) -> str:
    result = _decoder_instance.encode(data, fmt)
    return str(result.get("result", result)) if isinstance(result, dict) else str(result)
