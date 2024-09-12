import os
import shutil
import site
from pathlib import Path

import polarion

from enhancer import Loader

site_package_path = Path(__file__).parent.parent / "site-packages-changes"
polarion_location = Path(polarion.__file__)


def check_packages():
    loader = Loader("Checking packages... ", "All good.").start()
    for path in site.getsitepackages():
        path = Path(site.__file__).parent / "site-packages" / path
        if "site-packages" in str(path):
            for file in os.listdir(site_package_path / "polarion"):
                shutil.copy(site_package_path / "polarion" / file, path / "polarion" / file)
    loader.stop()
    print("Packages installed.")
    return


def print_instructions():
    print("\n1. Installing the necessary packages:")
    check_packages()


if __name__ == '__main__':
    print_instructions()
