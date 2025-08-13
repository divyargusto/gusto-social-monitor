#!/usr/bin/env python3
"""
Download required NLTK data with SSL certificate handling.
"""

import ssl
import nltk

# Handle SSL certificate issues on macOS
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
datasets = ['punkt', 'stopwords', 'wordnet', 'vader_lexicon', 'averaged_perceptron_tagger']

print("Downloading NLTK datasets...")
for dataset in datasets:
    try:
        nltk.download(dataset, quiet=True)
        print(f"✓ Downloaded {dataset}")
    except Exception as e:
        print(f"✗ Failed to download {dataset}: {e}")

print("NLTK data download complete!") 