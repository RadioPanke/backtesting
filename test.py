from util.conf import *
from io import StringIO
import requests
import pandas as pd
import yaml
from art import tprint





import re

def extract_text_between_parentheses(text):
    # Use regular expression to find all text between parentheses
    return re.findall(r'\((.*?)\)', text)

def write_to_file(text_list, filename):
    # Join the list with commas and write it to a file
    with open(filename, 'w') as file:
        file.write(','.join(text_list))

def read_from_file(filename):
    # Read the entire content of the file
    with open(filename, 'r') as file:
        return file.read()

# Example usage
input_file = "/Users/diego/asd"
output_file = "/Users/diego/out.csv"

# Read text from input file
input_text = read_from_file(input_file)

# Extract text between parentheses
extracted_text = extract_text_between_parentheses(input_text)

# Write the extracted text to a file
write_to_file(extracted_text, output_file)

print(f"Extracted text written to {output_file}")