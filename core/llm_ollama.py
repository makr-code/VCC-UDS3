#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDS3 Ollama LLM Client - Integration mit lokalem Ollama Server

Ollama: https://ollama.ai
- Lokal betriebene LLMs (keine Cloud)
- Unterstützt: Llama 2, Mistral, CodeLlama, etc.
- REST API: http://localhost:11434

Features:
- Streaming Support
- Temperature/Top-P Control
- Error Handling & Retries
- Token Counting (approximativ)
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional, Generator, Union
import time


class OllamaClient:
    """
    REST API Client für Ollama
    
    Beispiel:
    ```python
    client = OllamaClient()
    
    # Einfache Generation
    response = client.generate("Erkläre: Was ist eine Baugenehmigung?")
    print(response)
    
    # Streaming
    for chunk in client.generate_stream("Erkläre: Was ist eine Baugenehmigung?"):
        print(chunk, end="", flush=True)
    
    # Mit System Prompt
    response = client.generate(
        "Was sind die Schritte?",
        system_prompt="Du bist ein Experte für deutsche Verwaltungsprozesse.",
        model="mistral"
    )
    ```
    """
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "mistral"  # oder "llama2", "codellama", etc.
    
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        Initialisiert Ollama Client
        
        Args:
            base_url: Ollama Server URL (default: http://localhost:11434)
            default_model: Standard-Modell (default: mistral)
            timeout: Request Timeout in Sekunden
            max_retries: Maximale Anzahl Retries bei Fehler
            retry_delay: Wartezeit zwischen Retries (Sekunden)
        """
        self.logger = logging.getLogger('OllamaClient')
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_generated": 0,  # Approximation
            "total_time_seconds": 0.0
        }
        
        # Check Connection
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Prüft ob Ollama Server erreichbar ist
        
        Returns:
            True wenn erreichbar, sonst False
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.logger.info(f"✅ Ollama Server erreichbar: {len(models)} Modelle verfügbar")
                return True
            else:
                self.logger.warning(f"⚠️ Ollama Server antwortet mit Status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"⚠️ Ollama Server nicht erreichbar: {e}")
            self.logger.warning(f"   → Stelle sicher dass Ollama läuft: ollama serve")
            return False
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        raw: bool = False
    ) -> str:
        """
        Generiert Text mit Ollama (blocking)
        
        Args:
            prompt: User-Prompt
            model: Modell-Name (default: self.default_model)
            system_prompt: System-Prompt für Kontext
            temperature: Randomness (0.0 = deterministisch, 1.0 = kreativ)
            top_p: Nucleus Sampling (0.0 - 1.0)
            max_tokens: Maximale Anzahl Tokens (None = unbegrenzt)
            stop_sequences: Liste von Stop-Sequenzen
            raw: Raw mode (keine Template-Formatierung)
        
        Returns:
            Generierter Text
        """
        model = model or self.default_model
        
        # Build Request
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p
            },
            "raw": raw
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        if stop_sequences:
            request_data["options"]["stop"] = stop_sequences
        
        # Execute with Retries
        for attempt in range(self.max_retries):
            try:
                self.stats["total_requests"] += 1
                start_time = time.time()
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=request_data,
                    timeout=self.timeout
                )
                
                elapsed = time.time() - start_time
                self.stats["total_time_seconds"] += elapsed
                
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get("response", "")
                
                # Update Statistics
                self.stats["successful_requests"] += 1
                # Approximate token count (1 token ≈ 4 chars for German)
                approx_tokens = len(generated_text) // 4
                self.stats["total_tokens_generated"] += approx_tokens
                
                self.logger.debug(f"✅ Generated {approx_tokens} tokens in {elapsed:.2f}s")
                
                return generated_text
            
            except requests.exceptions.RequestException as e:
                self.stats["failed_requests"] += 1
                self.logger.warning(f"⚠️ Ollama Request fehlgeschlagen (Versuch {attempt+1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
        
        raise RuntimeError(f"Ollama Request fehlgeschlagen nach {self.max_retries} Versuchen")
    
    def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        raw: bool = False
    ) -> Generator[str, None, None]:
        """
        Generiert Text mit Ollama (streaming)
        
        Args:
            Siehe generate()
        
        Yields:
            Text-Chunks als Generator
        """
        model = model or self.default_model
        
        # Build Request
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p
            },
            "raw": raw
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        if stop_sequences:
            request_data["options"]["stop"] = stop_sequences
        
        # Execute Streaming Request
        try:
            self.stats["total_requests"] += 1
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            full_response = ""
            
            # Stream Response
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)
                        chunk_text = chunk_data.get("response", "")
                        if chunk_text:
                            full_response += chunk_text
                            yield chunk_text
                        
                        # Check if done
                        if chunk_data.get("done", False):
                            break
                    
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ JSON Decode Error: {e}")
                        continue
            
            # Update Statistics
            elapsed = time.time() - start_time
            self.stats["total_time_seconds"] += elapsed
            self.stats["successful_requests"] += 1
            approx_tokens = len(full_response) // 4
            self.stats["total_tokens_generated"] += approx_tokens
            
            self.logger.debug(f"✅ Streamed {approx_tokens} tokens in {elapsed:.2f}s")
        
        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"❌ Ollama Streaming fehlgeschlagen: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        Chat Completion (OpenAI-kompatibles Format)
        
        Args:
            messages: Liste von Message-Dicts [{"role": "user", "content": "..."}]
            model: Modell-Name
            temperature: Randomness
            top_p: Nucleus Sampling
            max_tokens: Max Tokens
            stream: Streaming aktivieren
        
        Returns:
            String (blocking) oder Generator (streaming)
        """
        model = model or self.default_model
        
        request_data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p
            }
        }
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        if stream:
            return self._chat_stream(request_data)
        else:
            return self._chat_blocking(request_data)
    
    def _chat_blocking(self, request_data: Dict) -> str:
        """Chat Completion (blocking)"""
        try:
            self.stats["total_requests"] += 1
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=request_data,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            self.stats["total_time_seconds"] += elapsed
            
            response.raise_for_status()
            
            result = response.json()
            message = result.get("message", {})
            content = message.get("content", "")
            
            # Update Statistics
            self.stats["successful_requests"] += 1
            approx_tokens = len(content) // 4
            self.stats["total_tokens_generated"] += approx_tokens
            
            return content
        
        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"❌ Chat Request fehlgeschlagen: {e}")
            raise
    
    def _chat_stream(self, request_data: Dict) -> Generator[str, None, None]:
        """Chat Completion (streaming)"""
        try:
            self.stats["total_requests"] += 1
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=request_data,
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)
                        message = chunk_data.get("message", {})
                        chunk_text = message.get("content", "")
                        if chunk_text:
                            full_response += chunk_text
                            yield chunk_text
                        
                        if chunk_data.get("done", False):
                            break
                    
                    except json.JSONDecodeError:
                        continue
            
            # Update Statistics
            elapsed = time.time() - start_time
            self.stats["total_time_seconds"] += elapsed
            self.stats["successful_requests"] += 1
            approx_tokens = len(full_response) // 4
            self.stats["total_tokens_generated"] += approx_tokens
        
        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"❌ Chat Streaming fehlgeschlagen: {e}")
            raise
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Modelle
        
        Returns:
            Liste von Modell-Infos
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ List Models fehlgeschlagen: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Client-Statistiken zurück
        
        Returns:
            Dict mit Statistiken
        """
        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
        
        avg_time = 0.0
        if self.stats["successful_requests"] > 0:
            avg_time = self.stats["total_time_seconds"] / self.stats["successful_requests"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "avg_time_per_request": avg_time,
            "base_url": self.base_url,
            "default_model": self.default_model
        }
    
    def __repr__(self):
        stats = self.get_stats()
        return (
            f"OllamaClient("
            f"url={self.base_url}, "
            f"model={self.default_model}, "
            f"requests={stats['total_requests']}, "
            f"success_rate={stats['success_rate']:.1%})"
        )


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing OllamaClient...")
    
    client = OllamaClient()
    
    # Test 1: List Models
    models = client.list_models()
    print(f"✅ Verfügbare Modelle: {[m['name'] for m in models]}")
    
    # Test 2: Simple Generation
    if models:
        prompt = "Erkläre in einem Satz: Was ist eine Baugenehmigung?"
        print(f"\n📝 Prompt: {prompt}")
        response = client.generate(prompt, temperature=0.3)
        print(f"🤖 Response: {response}")
        
        # Test 3: Streaming
        print(f"\n📝 Streaming...")
        for chunk in client.generate_stream("Zähle die Zahlen 1 bis 5.", temperature=0.1):
            print(chunk, end="", flush=True)
        print()
        
        # Test 4: Statistics
        stats = client.get_stats()
        print(f"\n✅ Stats: {stats}")
        
        print(f"\n{client}")
    else:
        print("⚠️ Keine Modelle verfügbar. Installiere Ollama: https://ollama.ai")
