import os
import json


__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'para_whitelist.json')) as data_file:
    whitelist = json.load(data_file)
