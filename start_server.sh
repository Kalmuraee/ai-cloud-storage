#!/bin/bash
export PYTHONPATH=/Users/iKhalidPro/Documents/BrainBox/BrainWorker/ai-cloud-storage
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
