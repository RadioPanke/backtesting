from util.conf import *
from io import StringIO
import requests
import pandas as pd
import yaml

with open(r'E:\data\fruits.yaml') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    fruits_list = yaml.load(file, Loader=yaml.FullLoader)

    print(fruits_list)