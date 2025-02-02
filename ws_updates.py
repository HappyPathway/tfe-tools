#!/usr/bin/env python3
import json
import semantic_version
import os
from collections import defaultdict
import re

def main():
    mod_report = json.loads(open(os.path.expandvars(os.path.join(os.path.dirname(__file__), "./reports/mod_update.json"))).read())
    for ws in sorted(mod_report.keys()):
        print(ws)

if __name__ == '__main__':
    main()