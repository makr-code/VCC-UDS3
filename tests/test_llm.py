#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llm.py

test_llm.py
Test Script für UDS3 Ollama LLM Client
import sys
import logging
logging.basicConfig(level=logging.INFO)
print('🧪 Testing UDS3 Ollama LLM Client...')
print()
from uds3.core.llm_ollama import OllamaClient
# Test 1: Initialize
print('1️⃣ Initialisiere Ollama Client...')
client = OllamaClient(default_model="llama3.1:8b")
print(f'   Base URL: {client.base_url}')
print(f'   Model: {client.default_model}')
print()
# Test 2: List Models
print('2️⃣ Liste verfügbare Modelle...')
models = client.list_models()
print(f'   Anzahl Modelle: {len(models)}')
for m in models[:3]:
print(f'   - {m["name"]}')
print()
# Test 3: Simple Generation
print('3️⃣ Einfache Text-Generation...')
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import sys
import logging
logging.basicConfig(level=logging.INFO)

print('🧪 Testing UDS3 Ollama LLM Client...')
print()

from uds3.core.llm_ollama import OllamaClient

# Test 1: Initialize
print('1️⃣ Initialisiere Ollama Client...')
client = OllamaClient(default_model="llama3.1:8b")
print(f'   Base URL: {client.base_url}')
print(f'   Model: {client.default_model}')
print()

# Test 2: List Models
print('2️⃣ Liste verfügbare Modelle...')
models = client.list_models()
print(f'   Anzahl Modelle: {len(models)}')
for m in models[:3]:
    print(f'   - {m["name"]}')
print()

# Test 3: Simple Generation
print('3️⃣ Einfache Text-Generation...')
prompt = "Erkläre in einem Satz: Was ist eine Baugenehmigung?"
print(f'   Prompt: {prompt}')
response = client.generate(prompt, temperature=0.3, max_tokens=100)
print(f'   Response: {response[:200]}...')
print()

# Test 4: Streaming (erste 3 Chunks)
print('4️⃣ Streaming Test...')
prompt = "Zähle die Zahlen 1 bis 5."
print(f'   Prompt: {prompt}')
print('   Response: ', end='', flush=True)
chunk_count = 0
for chunk in client.generate_stream(prompt, temperature=0.1, max_tokens=50):
    print(chunk, end='', flush=True)
    chunk_count += 1
    if chunk_count > 50:  # Limit für Test
        break
print()
print()

# Test 5: Chat Completion
print('5️⃣ Chat Completion...')
messages = [
    {"role": "system", "content": "Du bist ein Experte für deutsche Verwaltungsprozesse."},
    {"role": "user", "content": "Was sind die Hauptschritte einer Baugenehmigung? Antworte kurz."}
]
response = client.chat(messages, temperature=0.5, max_tokens=150)
print(f'   Response: {response[:300]}...')
print()

# Test 6: Statistics
print('6️⃣ Client Statistics...')
stats = client.get_stats()
print(f'   Total Requests: {stats["total_requests"]}')
print(f'   Successful: {stats["successful_requests"]}')
print(f'   Failed: {stats["failed_requests"]}')
print(f'   Success Rate: {stats["success_rate"]:.1%}')
print(f'   Avg Time: {stats["avg_time_per_request"]:.2f}s')
print()

print('✅ Alle Tests erfolgreich!')
print(f'📊 {client}')
