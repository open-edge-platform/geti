// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

//! The backend's self-signed TLS certificate.

use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use sha2::{Digest, Sha256};
use tauri::AppHandle;

/// Read the certificate the backend serves, `<data dir>/certs/localhost.pem`
/// (see `application/backend/app/main.py`).
pub fn read_pem(app: &AppHandle) -> Result<Vec<u8>, String> {
    let path = crate::resolve_data_dir(app)
        .ok_or("unknown data directory")?
        .join("certs")
        .join("localhost.pem");
    std::fs::read(&path).map_err(|e| format!("{}: {e}", path.display()))
}

/// Base64 SHA-256 of the certificate's DER SubjectPublicKeyInfo, the format of
/// Chromium's `--ignore-certificate-errors-spki-list`.
pub fn spki_sha256(pem: &[u8]) -> Option<String> {
    let der = pem_to_der(pem)?;
    Some(STANDARD.encode(Sha256::digest(subject_public_key_info(&der)?)))
}

fn pem_to_der(pem: &[u8]) -> Option<Vec<u8>> {
    let body = std::str::from_utf8(pem)
        .ok()?
        .split("-----BEGIN CERTIFICATE-----")
        .nth(1)?
        .split("-----END CERTIFICATE-----")
        .next()?;
    STANDARD
        .decode(body.split_whitespace().collect::<String>())
        .ok()
}

/// The whole SubjectPublicKeyInfo element of a DER certificate (RFC 5280, 4.1).
fn subject_public_key_info(certificate: &[u8]) -> Option<&[u8]> {
    let (_, certificate, _) = der_element(certificate)?;
    let (_, mut tbs, _) = der_element(certificate)?;
    // Skip the optional [0] version, then serialNumber, signature, issuer, validity and subject.
    if tbs.first() == Some(&0xA0) {
        tbs = der_element(tbs)?.2;
    }
    for _ in 0..5 {
        tbs = der_element(tbs)?.2;
    }
    let (spki, _, _) = der_element(tbs)?;
    (spki.first() == Some(&0x30)).then_some(spki)
}

/// Split the DER element at the start of `input` into (element, contents, rest of input).
fn der_element(input: &[u8]) -> Option<(&[u8], &[u8], &[u8])> {
    let (&length, rest) = input.get(1..)?.split_first()?;
    let (length, rest) = if length < 0x80 {
        (usize::from(length), rest)
    } else {
        let count = usize::from(length & 0x7f);
        if count == 0 || count > 4 {
            return None;
        }
        let bytes = rest.get(..count)?;
        let length = bytes.iter().fold(0, |acc, &b| (acc << 8) | usize::from(b));
        (length, &rest[count..])
    };
    let header = input.len() - rest.len();
    let element = input.get(..header.checked_add(length)?)?;
    Some((element, &element[header..], &input[element.len()..]))
}

#[cfg(test)]
mod tests {
    use super::{pem_to_der, spki_sha256, subject_public_key_info};

    /// Generated like `application/backend/pyinstaller/windows/certs.py` does.
    const CERTIFICATE: &str = "-----BEGIN CERTIFICATE-----
MIIC1DCCAbygAwIBAgIUHIY0FEhKFhEKWQ2A5T8l5lg5248wDQYJKoZIhvcNAQEL
BQAwFDESMBAGA1UEAwwJbG9jYWxob3N0MB4XDTI2MTEwOTA2MzczOFoXDTM2MTEw
NzA2MzczOFowFDESMBAGA1UEAwwJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEF
AAOCAQ8AMIIBCgKCAQEAxVo4pwcS+FeIUFGQDjoOnkiEjI38VKFzyIit8CmEx8r4
mf724y47KQQJMeHZlpC2ucwPsdmVsFQo5SeyiEzCoi0TCYXyAv+yHb+pXZhWxvwx
TwfX8oRoSOzQxqzq1Y1dmsDO4JUJzK65fU1RgQtif8b6+QXRDnkgLJ86NoCzZ8FO
ssZJ0p00rkhf90fkPXIpLnBxn39I3Ag8pT2IoNRCf7o6d70KyCXOZ8nlRcWkJYN3
GRTSED93WRL/C5OINBwlZ0FU6T33ILbNdU06K/YsX8wt8T9XUY3jNByzYofQdnvx
gdPdLAkodDahPXQDPS0pZ4nL5scyYhPVXwZTi9LYXwIDAQABox4wHDAaBgNVHREE
EzARgglsb2NhbGhvc3SHBH8AAAEwDQYJKoZIhvcNAQELBQADggEBAMT9L7egsPOP
fde99MtIsO7jymsJ/qdYu/BGp52bpa3NoRqHWjuhKi63Nhx0bjHS8O5EeYT0phs6
4DvKviSZ6x2+4AnJAS8vK+Y74kahcvucRnWLZRx+M7zH2uSmHCB3n/MoNgUwAdLR
kRU+GW7I9DCA7GKtFZIFkfxmJ0qiD1CDShnz3P335WQeFVmz2B3ypMQ2DL3ldj+v
LnBCDtDLbaZt+NTLIGQPexUGXUwhBer6F1bS/XAWiNzFWLnAnGlbEX2Mx+xJ5We3
FI025bZWNDUeizmu2FbLfqrkxtI7VnFSKfoCT3RXpz/S6yqLO+cvtlqgj5a/xdll
IgQy7HwOKgg=
-----END CERTIFICATE-----
";

    #[test]
    fn hashes_the_public_key() {
        // Computed with Python's `cryptography` and accepted by WebView2.
        assert_eq!(
            spki_sha256(CERTIFICATE.as_bytes()).as_deref(),
            Some("fBiYWICQ99Bc4Qqqt9619pJM0bp/KzrV9WGjBOke79Q=")
        );
    }

    #[test]
    fn rejects_malformed_certificates() {
        let truncated = CERTIFICATE.replacen("IgQy7HwOKgg=", "", 1);
        for pem in ["", "not a certificate", &truncated] {
            assert_eq!(spki_sha256(pem.as_bytes()), None, "{pem:?}");
        }
    }

    #[test]
    fn never_panics_on_corrupted_der() {
        let der = pem_to_der(CERTIFICATE.as_bytes()).unwrap();
        for end in 0..der.len() {
            assert_eq!(subject_public_key_info(&der[..end]), None);
        }
        for index in 0..der.len() {
            for value in [0x00, 0x7f, 0x80, 0x84, 0xff] {
                let mut corrupted = der.clone();
                corrupted[index] = value;
                let _ = subject_public_key_info(&corrupted);
            }
        }
    }
}
