# install_certifi.py
#
# sample script to install or update a set of default Root Certificates
# for the ssl module.  Uses the certificates provided by the certifi package:
#       https://pypi.python.org/pypi/certifi
#
# * this script is meant to be used on OSX when
#   following this howto: https://github.com/qgiscloud/qgis-cloud-plugin/wiki/Resolving-certificate-problems-on-OSX
#
# * it was copied from:
#
#   https://gist.githubusercontent.com/marschhuynh/31c9375fc34a3e20c2d3b9eb8131d8f3/raw/7f1332892a48e611bffeaba4ae5b827f2b6f4924/Install%2520Certificates.command 
#
# * the script originates from the certify package.
#
# * it has been adapted by tpo_deb@sourcepole.ch *not* to
#   upgrade the `certifi` package via `pip` since that
#   step failed when executed. This step should not be
#   necessary, since getting an updated `certifi`
#   package is part of a previous step in the mentioned
#   howto.
#

import os
import os.path
import ssl
import stat
import subprocess
import sys

STAT_0o775 = ( stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
             | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
             | stat.S_IROTH |                stat.S_IXOTH )


def main():
    openssl_dir, openssl_cafile = os.path.split(
        ssl.get_default_verify_paths().openssl_cafile)

    print("Dir: ", openssl_dir)

    # print(" -- pip install --upgrade certifi")
    # subprocess.check_call([sys.executable,
    #     "-E", "-s", "-m", "pip", "install", "--upgrade", "certifi"])

    import certifi

    # change working directory to the default SSL directory
    os.chdir(openssl_dir)
    relpath_to_certifi_cafile = os.path.relpath(certifi.where())
    print(" -- removing any existing file or link")
    try:
        os.remove(openssl_cafile)
    except FileNotFoundError:
        pass
    print(" -- creating symlink to certifi certificate bundle")
    os.symlink(relpath_to_certifi_cafile, openssl_cafile)
    print(" -- setting permissions")
    os.chmod(openssl_cafile, STAT_0o775)
    print(" -- update complete")

if __name__ == '__main__':
    main()
