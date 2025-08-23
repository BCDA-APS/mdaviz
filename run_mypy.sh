#!/bin/bash
# Run mypy with the correct parameters to avoid module path conflicts
cd src && python -m mypy --package mdaviz
