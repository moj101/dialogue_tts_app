# -*- coding: utf-8 -*-
"""
ماژول ارتباط با AvalAI API
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

from config import DEFAULT_BASE_URL, DEFAULT_TTS_MODEL


class AvalaiAPI:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    # ---------------------------------------------------------
    # ابزارهای داخلی
    # ---------------------------------------------------------
    def _full_url(self, path: str) -> str:
        path = path.strip()
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _user_api_url(self, path: str) -> str:
        root = self.base_url
        if root.endswith("/v1"):
            root = root[:-3]
        if not path.startswith("/"):
            path = "/" + path
        return f"{root}{path}"

    def _safe_json(self, response: requests.Response) -> Any:
        try:
            return response.json()
        except Exception:
            try:
                return response.text
            except Exception:
                return ""

    def _extract_request_id_from_headers(self, response: requests.Response) -> str:
        return (
            response.headers.get("x-request-id")
            or response.headers.get("X-Request-Id")
            or response.headers.get("X-Request-ID")
            or ""
        ).strip()

    # ---------------------------------------------------------
    # تست اتصال
    # ---------------------------------------------------------
    def test_connection(self) -> bool:
        if not self.api_key:
            return False

        try:
            url = self._full_url("/models")
            response = self.session.get(url, timeout=20)
            return response.status_code in (200, 401, 403)
        except Exception:
            return False

    # ---------------------------------------------------------
    # تبدیل متن به گفتار
    # ---------------------------------------------------------
    def text_to_speech(
        self,
        model: str,
        voice: str,
        text: str,
        speed: float,
        output_file: Path,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("API key خالی است.")

        model = (model or DEFAULT_TTS_MODEL).strip()
        voice = (voice or "nova").strip()
        text = (text or "").strip()

        if not text:
            raise ValueError("متن برای تبدیل به گفتار خالی است.")

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        url = self._full_url("/audio/speech")

        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "speed": speed,
        }

        response = self.session.post(url, data=json.dumps(payload), timeout=180)
        request_id = self._extract_request_id_from_headers(response)
        raw_response = self._safe_json(response)

        if response.status_code >= 400:
            raise requests.HTTPError(
                f"TTS request failed: {response.status_code} - {raw_response}",
                response=response,
            )

        output_file.write_bytes(response.content)

        return {
            "success": True,
            "output_file": str(output_file),
            "request_id": request_id,
            "status_code": response.status_code,
            "raw_response": raw_response if isinstance(raw_response, str) else json.dumps(raw_response, ensure_ascii=False),
        }

    # ---------------------------------------------------------
    # lookup هزینه تراکنش
    # ---------------------------------------------------------
    def lookup_transaction_cost(self, request_id: str) -> Dict[str, Any]:
        request_id = (request_id or "").strip()
        if not request_id:
            raise ValueError("request_id خالی است.")

        url = self._user_api_url("/user/v1/transactions/lookup")
        payload = {
            "transaction_ids": [request_id]
        }

        response = self.session.post(url, data=json.dumps(payload), timeout=30)
        raw = self._safe_json(response)

        if response.status_code >= 400:
            raise requests.HTTPError(
                f"Lookup failed: {response.status_code} - {raw}",
                response=response,
            )

        if isinstance(raw, dict):
            raw["_lookup_request_id"] = request_id

        return raw

    def lookup_transaction_cost_with_retry(
        self,
        request_id: str,
        retries: int = 6,
        delay_seconds: int = 5,
    ) -> Dict[str, Any]:
        last_error: Optional[Exception] = None

        for attempt in range(1, retries + 1):
            try:
                data = self.lookup_transaction_cost(request_id)
                result = self.extract_costs_from_lookup(data)
                result["attempt"] = attempt

                has_cost = bool(result.get("cost_usd") or result.get("cost_irr"))
                has_tx = bool(result.get("transaction_id"))

                result["ready"] = has_cost
                if has_cost or has_tx:
                    return result

            except Exception as e:
                last_error = e

            if attempt < retries:
                time.sleep(delay_seconds)

        if last_error:
            raise last_error

        return {
            "transaction_id": request_id,
            "cost_usd": "",
            "cost_irr": "",
            "raw_response": "",
            "attempt": retries,
            "ready": False,
        }

    # ---------------------------------------------------------
    # استخراج هزینه از پاسخ lookup
    # ---------------------------------------------------------
    def extract_costs_from_lookup(self, data: Any) -> Dict[str, str]:
        result = {
            "transaction_id": "",
            "cost_usd": "",
            "cost_irr": "",
            "raw_response": json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data,
        }

        if isinstance(data, str):
            return result

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = None
            for key in ("data", "items", "results", "transactions"):
                value = data.get(key)
                if isinstance(value, list):
                    items = value
                    break

            if items is None and any(k in data for k in ("transaction_id", "id", "cost_usd", "cost_irr", "price")):
                items = [data]

            if items is None:
                return result
        else:
            return result

        if not items:
            return result

        item = items[0]
        if not isinstance(item, dict):
            return result

        transaction_id = (
            item.get("transaction_id")
            or item.get("id")
            or item.get("request_id")
            or ""
        )

        cost_usd = (
            item.get("cost_usd")
            or item.get("usd_cost")
            or item.get("price_usd")
            or item.get("amount_usd")
            or ""
        )

        cost_irr = (
            item.get("cost_irr")
            or item.get("irr_cost")
            or item.get("price_irr")
            or item.get("amount_irr")
            or item.get("cost_toman")
            or item.get("cost_rial")
            or ""
        )

        if not cost_usd and "cost" in item and isinstance(item.get("cost"), (str, int, float)):
            cost_usd = str(item.get("cost"))

        result["transaction_id"] = str(transaction_id or "")
        result["cost_usd"] = str(cost_usd or "")
        result["cost_irr"] = str(cost_irr or "")
        return result