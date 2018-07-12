#!/usr/bin/env python3

import sys

if __name__ == "__main__" :

    if len(sys.argv) > 1 :
        (req_major, dot, req_minor, dot, patch ) = sys.argv[1].partition(".")
        installed_major = sys.version_info.major
        installed_minor = sys.version_info.minor

        if req_major and int(req_major) > installed_major:
            print( "required major version is {} installed major version is {}".format( req_major, installed_major))
            sys.exit(1)

        if req_minor and int(req_minor) > installed_minor:
            print( "required minor version is {} installed version is {}".format( req_minor, installed_minor))
            sys.exit(1)

print( "{}.{} is good to go".format( req_major, req_minor))

sys.exit(0)