"""
ClassRoom Manager - TLS/SSL konfiqurasiyası və təhlükəsizlik.
"""
from __future__ import annotations

import ssl
import logging
import hashlib
import secrets
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def create_server_ssl_context(certfile: str = None, keyfile: str = None) -> ssl.SSLContext:
    """Server üçün SSL konteksti yaradır."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    if certfile and keyfile and os.path.exists(certfile) and os.path.exists(keyfile):
        ctx.load_cert_chain(certfile, keyfile)
        logger.info("TLS sertifikat yükləndi")
    else:
        cert_path, key_path = _generate_self_signed_cert()
        ctx.load_cert_chain(cert_path, key_path)
        logger.info("Öz-imzalı TLS sertifikat yaradıldı")

    return ctx


def create_client_ssl_context() -> ssl.SSLContext:
    """Client üçün SSL konteksti yaradır (öz-imzalı sertifikatları qəbul edir)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def _generate_self_signed_cert() -> tuple[str, str]:
    """Öz-imzalı sertifikat yaradır (openssl vasitəsilə)."""
    cert_dir = Path.home() / ".classroom_manager" / "certs"
    cert_dir.mkdir(parents=True, exist_ok=True)

    cert_path = cert_dir / "server.crt"
    key_path = cert_dir / "server.key"

    if cert_path.exists() and key_path.exists():
        return str(cert_path), str(key_path)

    try:
        import subprocess
        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", str(key_path),
                "-out", str(cert_path),
                "-days", "365",
                "-nodes",
                "-subj", "/CN=ClassRoomManager/O=ClassRoom/C=AZ",
            ],
            capture_output=True,
            check=True,
        )
        logger.info(f"Sertifikat yaradıldı: {cert_path}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"OpenSSL ilə sertifikat yaradıla bilmədi: {e}")
        # Fallback: Python ilə yaradırıq
        _generate_cert_python(cert_path, key_path)

    return str(cert_path), str(key_path)


def _generate_cert_python(cert_path: Path, key_path: Path) -> None:
    """Python vasitəsilə öz-imzalı sertifikat yaradır (cryptography kitabxanası lazımdır)."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta, timezone

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "ClassRoomManager"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ClassRoom"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "AZ"),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        logger.info("Python ilə sertifikat yaradıldı")
    except ImportError:
        logger.error("cryptography kitabxanası tapılmadı, TLS-siz davam edilir")


def verify_pre_shared_key(received_key: str, stored_key: str) -> bool:
    """Pre-shared key yoxlayır (timing attack-dan qorunmaq üçün)."""
    received_hash = hashlib.sha256(received_key.encode()).hexdigest()
    stored_hash = hashlib.sha256(stored_key.encode()).hexdigest()
    return secrets.compare_digest(received_hash, stored_hash)


def hash_key(key: str) -> str:
    """Açarın hash-ini qaytarır."""
    return hashlib.sha256(key.encode()).hexdigest()
