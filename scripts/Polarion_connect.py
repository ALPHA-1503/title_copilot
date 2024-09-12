import os
from polarion.polarion import Polarion
from dotenv import load_dotenv
from pathlib import Path

from scripts.file_helper import path_to_certs, current_path

load_dotenv()
cert_path = current_path.parent.parent / 'certif' / 'ca-certificates.crt'

def get_polarion_client_dev():
    client = Polarion(
    os.environ.get("polarion_url_dev"),
    user=os.environ.get("polarion_user"),
    password=os.environ.get("polarion_password"),
    token=None,
    verify_certificate = str(cert_path)
)
    return client

def get_polarion_client_uat():
    client = Polarion(
    os.environ.get("polarion_url_uat"),
    user=os.environ.get("polarion_user"),
    password=os.environ.get("polarion_password"),
    token=None,
    verify_certificate = str(cert_path)
)
    return client