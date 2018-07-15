#!/usr/bin/env python3

import sys

if __name__ == "__main__" :

    if len(sys.argv) > 1 :
        req_info = sys.argv[1].split(".", 3 )
        installed_major = sys.version_info.major
        installed_minor = sys.version_info.minor

        if len(req_info) > 0 and int(req_info[0]) > installed_major:
            print( "Required major version is {}, installed major version is {}".format( req_info[0], installed_major))
            sys.exit(1)

        if len(req_info) > 1 and int(req_info[1]) > installed_minor:
            print( "Required minor version is {}, installed minor version is {}".format( req_info[1], installed_minor))
            sys.exit(1)

if len(req_info) > 1 :
    print( "{}.{} is good to go".format( req_info[0], req_info[1]))
else:
    print("{} is good to go".format( req_info[0]))

sys.exit(0)