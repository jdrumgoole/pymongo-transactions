"""

Program to test feature compatibility for MongoDB 4.0
======================================================

For new installations of MongoDB 4.0 installed into an empty database the
featureCompatibilityVersion version is set to "4.0" by default.

However if you install over an existing MongoDB 3.6 /data directory then
featureCompatibilityVersion is set to "3.6".

This program allows you to both query and set the featureCompatibilityVersion.

It has only be tested on MongoDB 4.0.

"""
import pymongo

from argparse import ArgumentParser


if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("--host", default="mongodb://localhost:27100/?replicaSet=txntest",
                        help="MongoDB URI [default: %(default)s]")
    parser.add_argument("--feature_version",
                        help="Server the server featureCompatibilityVersion (also try '4.0' for transactions [default: %(default)s]")

    args = parser.parse_args()

    c = pymongo.MongoClient(args.host)

    doc = c.admin.command({"getParameter": 1, "featureCompatibilityVersion": 1})
    print("Current featureCompatibilityVersion: '{}'".format(doc["featureCompatibilityVersion"]["version"]))

    if args.feature_version:
        c.admin.command({"setFeatureCompatibilityVersion": args.feature_version})
        doc = c.admin.command({"getParameter": 1, "featureCompatibilityVersion": 1})
        print("New featureCompatibilityVersion: '{}'".format(doc["featureCompatibilityVersion"]["version"]))
