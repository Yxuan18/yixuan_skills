# -*- coding: utf-8 -*-
"""
Tests for cve-http-filter/cve_http_filter.py
All network calls are mocked.
"""
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cve-http-filter"))

from cve_http_filter import extract_cves, filter_and_output, _get_session, get_proxy, query_nvd


class TestExtractCves:
    def test_extracts_cve_id_and_desc_and_poc(self):
        content = """## CVE-2024-1234
Some vulnerability description here.
- POC: https://github.com/user/repo/blob/main/poc.py

## CVE-2024-5678
Another vulnerability.
"""
        cves = extract_cves(content)
        assert len(cves) == 2
        assert cves[0]["id"] == "CVE-2024-1234"
        assert "Some vulnerability" in cves[0]["desc"]
        assert "github.com/user/repo" in cves[0]["poc"]
        assert cves[1]["id"] == "CVE-2024-5678"

    def test_handles_empty_content(self):
        assert extract_cves("") == []

    def test_handles_no_poc(self):
        cves = extract_cves("## CVE-2024-9999\nNo POC here.\n")
        assert len(cves) == 1
        assert cves[0]["poc"] == ""

    def test_skips_list_items_in_description(self):
        content = """## CVE-2024-0001
- list item one
- list item two
![image](url)
Real description text."""
        assert extract_cves(content)[0]["desc"] == "Real description text."


class TestFilterAndOutput:
    def test_filters_avn_only(self):
        cves = [
            {"id": "CVE-2024-1", "av": "AV:N", "score": 9.0, "desc": "a"},
            {"id": "CVE-2024-2", "av": "AV:L", "score": 7.0, "desc": "b"},
            {"id": "CVE-2024-3", "av": "AV:N", "score": 8.5, "desc": "c"},
            {"id": "CVE-2024-4", "av": "AV:P", "score": 9.5, "desc": "d"},
        ]
        avn, rest = filter_and_output(cves)
        assert len(avn) == 2
        assert len(rest) == 2
        # Sorted by score descending
        assert avn[0]["id"] == "CVE-2024-1"
        assert avn[1]["id"] == "CVE-2024-3"

    def test_av_field_missing_goes_to_rest(self):
        """CVE with no av field goes to rest, not avn."""
        cves = [{"id": "CVE-2024-1", "score": 8.0}]
        avn, rest = filter_and_output(cves)
        assert len(avn) == 0
        assert len(rest) == 1

    def test_av_n_a_goes_to_rest(self):
        """av='N/A' is not 'AV:N' so goes to rest."""
        cves = [{"id": "CVE-2024-1", "av": "N/A", "score": 8.0}]
        avn, rest = filter_and_output(cves)
        assert len(avn) == 0
        assert len(rest) == 1


class TestGetSession:
    def test_session_without_proxy(self, monkeypatch):
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            monkeypatch.delenv(var, raising=False)
        session = _get_session()
        assert session.proxies == {}

    def test_session_with_http_proxy(self, monkeypatch):
        monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
        monkeypatch.delenv("HTTPS_PROXY", raising=False)
        session = _get_session()
        assert session.proxies["http"] == "http://proxy:8080"
        assert session.proxies["https"] == "http://proxy:8080"

    def test_session_with_https_proxy(self, monkeypatch):
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy:8080")
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        session = _get_session()
        assert session.proxies["http"] == "http://proxy:8080"


class TestGetProxy:
    def test_prefers_http_over_https(self, monkeypatch):
        monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy2:8080")
        # Fresh import to avoid module-cached state
        import importlib, cve_http_filter
        importlib.reload(cve_http_filter)
        assert cve_http_filter.get_proxy() == "http://proxy:8080"

    def test_falls_back_to_https(self, monkeypatch):
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy:8080")
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        import importlib, cve_http_filter
        importlib.reload(cve_http_filter)
        assert cve_http_filter.get_proxy() == "http://proxy:8080"

    def test_returns_none_when_no_proxy(self, monkeypatch):
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            monkeypatch.delenv(var, raising=False)
        import importlib, cve_http_filter
        importlib.reload(cve_http_filter)
        assert cve_http_filter.get_proxy() is None

    def test_handles_lowercase(self, monkeypatch):
        # Clear ALL proxy vars first — get_proxy checks in specific order
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            monkeypatch.delenv(var, raising=False)
        # Now only set the lowercase variant
        monkeypatch.setenv("http_proxy", "http://proxy:8080")
        import importlib, cve_http_filter
        importlib.reload(cve_http_filter)
        assert cve_http_filter.get_proxy() == "http://proxy:8080"


class TestQueryNvd:
    def _mock_session(self, json_data, status_code=200):
        """Return a mock session whose .get() returns the given json_data."""
        session = pytest.importorskip("requests").Session()
        mock_resp = pytest.importorskip("requests").Response()
        mock_resp.status_code = status_code
        mock_resp._content = b"{}"
        mock_resp.json = lambda: json_data
        session.get = lambda *args, **kwargs: mock_resp
        return session

    def test_extracts_av_n_from_vector(self):
        mock_resp = {
            "vulnerabilities": [{
                "cve": {
                    "metrics": {
                        "cvssMetricV31": [{
                            "cvssData": {
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                                "baseScore": 10.0,
                            }
                        }]
                    }
                }
            }]
        }
        session = self._mock_session(mock_resp)
        result = query_nvd(session, "CVE-2024-1234")
        assert result["score"] == 10.0
        assert result["av"] == "AV:N"

    def test_extracts_av_l_from_vector(self):
        mock_resp = {
            "vulnerabilities": [{
                "cve": {
                    "metrics": {
                        "cvssMetricV30": [{
                            "cvssData": {
                                "vectorString": "CVSS:3.0/AV:L/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
                                "baseScore": 3.5,
                            }
                        }]
                    }
                }
            }]
        }
        session = self._mock_session(mock_resp)
        result = query_nvd(session, "CVE-2024-5678")
        assert result["av"] == "AV:L"
        assert result["score"] == 3.5

    def test_returns_n_a_when_cve_not_found(self):
        session = self._mock_session({"vulnerabilities": []})
        result = query_nvd(session, "CVE-2099-99999")
        assert result["av"] == "N/A"

    def test_returns_no_cvss_when_no_metrics(self):
        session = self._mock_session({"vulnerabilities": [{"cve": {"metrics": {}}}]})
        result = query_nvd(session, "CVE-2024-1")
        assert result["av"] == "NO_CVSS"

    def test_raises_on_network_error_after_retries(self):
        import requests as _req

        session = _req.Session()
        session.get = lambda *a, **kw: (_ for _ in ()).throw(_req.RequestException("conn reset"))
        with pytest.raises(_req.RequestException):
            query_nvd(session, "CVE-2024-1", retries=2)

    def test_retries_on_429_rate_limit(self):
        import requests as _req

        mock_429 = _req.Response()
        mock_429.status_code = 429
        mock_200 = _req.Response()
        mock_200.status_code = 200
        mock_200.json = lambda: {
            "vulnerabilities": [{
                "cve": {
                    "metrics": {
                        "cvssMetricV31": [{
                            "cvssData": {
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                                "baseScore": 9.8,
                            }
                        }]
                    }
                }
            }]
        }
        mock_200._content = b"{}"

        session = _req.Session()
        mock_responses = [mock_429, mock_429, mock_200]
        session.get = lambda *a, **kw: mock_responses.pop(0)

        result = query_nvd(session, "CVE-2024-1", retries=3)
        assert result["score"] == 9.8
