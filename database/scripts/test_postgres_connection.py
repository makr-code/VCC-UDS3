#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_postgres_connection.py

Test connectivity to PostgreSQL instance.
Tries psycopg2 if available, otherwise does a TCP probe.

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import sys
import socket
import traceback

HOST = '192.168.178.94'
PORT = 5432

print('Testing PostgreSQL connectivity to', f'{HOST}:{PORT}')

# Try psycopg2
try:
    import psycopg2
    print('psycopg2 available')
    try:
        conn = psycopg2.connect(host=HOST, port=PORT, user='postgres', password='', dbname='postgres', connect_timeout=5)
        print('psycopg2 connect succeeded')
        conn.close()
    except Exception as e:
        print('psycopg2 connect failed:', e)
except Exception as e:
    print('psycopg2 not available:', e)
    traceback.print_exc()

# TCP probe
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((HOST, PORT))
    print('TCP connect succeeded')
    s.close()
except Exception as e:
    print('TCP connect failed:', e)

print('Done')
