"""
WebAuthn / Passkey helpers.

This module wraps py-webauthn to provide:
  - Registration challenge generation
  - Registration response verification
  - Authentication challenge generation
  - Authentication response verification

References:
  https://www.w3.org/TR/webauthn-2/
  https://github.com/duo-labs/py_webauthn
"""

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

from app.config import get_settings


def build_registration_options(user_id: str, user_name: str, user_display_name: str):
    """Generate WebAuthn registration options to send to the browser."""
    cfg = get_settings()
    return generate_registration_options(
        rp_id=cfg.webauthn_rp_id,
        rp_name=cfg.webauthn_rp_name,
        user_id=user_id.encode(),
        user_name=user_name,
        user_display_name=user_display_name,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )


def verify_registration(registration_response: dict, expected_challenge: bytes):
    """Verify a registration response from the browser and return the credential."""
    cfg = get_settings()
    return verify_registration_response(
        credential=registration_response,
        expected_challenge=expected_challenge,
        expected_rp_id=cfg.webauthn_rp_id,
        expected_origin=cfg.webauthn_origin,
    )


def build_authentication_options(
    existing_credentials: list[dict] | None = None,
):
    """Generate WebAuthn authentication options to send to the browser."""
    cfg = get_settings()
    allow_credentials = []
    if existing_credentials:
        allow_credentials = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c["credential_id"]))
            for c in existing_credentials
        ]
    return generate_authentication_options(
        rp_id=cfg.webauthn_rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )


def verify_authentication(
    authentication_response: dict,
    expected_challenge: bytes,
    credential_public_key: bytes,
    credential_current_sign_count: int,
):
    """Verify an authentication response from the browser."""
    cfg = get_settings()
    return verify_authentication_response(
        credential=authentication_response,
        expected_challenge=expected_challenge,
        expected_rp_id=cfg.webauthn_rp_id,
        expected_origin=cfg.webauthn_origin,
        credential_public_key=credential_public_key,
        credential_current_sign_count=credential_current_sign_count,
    )


def encode_bytes(b: bytes) -> str:
    return bytes_to_base64url(b)


def decode_base64url(s: str) -> bytes:
    return base64url_to_bytes(s)
