#!/bin/bash
celery -A mysite worker --loglevel=INFO -E
