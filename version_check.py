#!/usr/bin/env python3

import sys

if __name__ == "__main__" :

    if len(sys.argv) > 1 :
        #print(sys.argv[1])
        versions = sys.argv[1].split(".",5)
        installed_major = sys.version_info.major
        installed_minor = sys.version_info.minor

        if versions and int(versions[0]) < installed_major:
            print( "required major version is {} installed major version is {}".format( versions[0], installed_major))
            sys.exit(1)

        if versions and int(versions[1]) < installed_minor:
            print( "required minor version is {} installed version is {}".format( versions[1], installed_minor))
            sys.exit(1)

    if versions:
        print( "{}.{} is good to go".format( versions[0], versions[1]))

sys.exit(0)