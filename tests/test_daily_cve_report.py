# -*- coding: utf-8 -*-
"""
Tests for daily-cve-report scripts.
All network calls are mocked.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "daily-cve-report" / "scripts"))

from fetch_cves import (
    _get_cvss,
    _get_description,
    _get_cwes,
    _get_affected,
    _get_references,
    _build_iocs,
    _process_cve,
    fetch_cves,
    IOC_TEMPLATES,
)
from format_report import format_cve_section, format_report


class TestGetCvss:
    def test_prefers_v31_over_v30(self):
        cve = {
            "metrics": {
                "cvssMetricV31": [{"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}],
                "cvssMetricV30": [{"cvssData": {"baseScore": 9.0, "baseSeverity": "HIGH"}}],
            }
        }
        score, sev = _get_cvss(cve)
        assert score == 9.8
        assert sev == "CRITICAL"

    def test_falls_back_to_v30(self):
        cve = {
            "metrics": {
                "cvssMetricV30": [{"cvssData": {"baseScore": 7.5, "baseSeverity": "HIGH"}}],
            }
        }
        score, sev = _get_cvss(cve)
        assert score == 7.5

    def test_falls_back_to_v2(self):
        cve = {
            "metrics": {
                "cvssMetricV2": [{"cvssData": {"baseScore": 5.0, "baseSeverity": ""}}],
            }
        }
        score, sev = _get_cvss(cve)
        assert score == 5.0

    def test_returns_none_when_no_metrics(self):
        cve = {"metrics": {}}
        score, sev = _get_cvss(cve)
        assert score is None
        assert sev == ""


class TestGetDescription:
    def test_prefers_english(self):
        cve = {
            "descriptions": [
                {"lang": "zh", "value": "中文描述"},
                {"lang": "en", "value": "English description"},
            ]
        }
        assert _get_description(cve) == "English description"

    def test_returns_fallback_when_no_english(self):
        cve = {"descriptions": [{"lang": "fr", "value": "Description française"}]}
        assert _get_description(cve) == "No description available."

    def test_returns_fallback_when_empty(self):
        assert _get_description({}) == "No description available."


class TestGetCwes:
    def test_extracts_cwe_ids(self):
        cve = {
            "weaknesses": [
                {"description": [{"value": "CWE-89"}]},
                {"description": [{"value": "CWE-79"}]},
                {"description": [{"value": "CWE-89"}]},  # duplicate
            ]
        }
        cwes = _get_cwes(cve)
        assert cwes == ["CWE-89", "CWE-79"]

    def test_handles_empty_weaknesses(self):
        assert _get_cwes({}) == []


class TestGetAffected:
    def test_extracts_vendor_product_version(self):
        cve = {
            "configurations": [{
                "nodes": [{
                    "cpeMatch": [{
                        "criteria": "cpe:2.3:a:apache:tomcat:9.0.0:*:*:*:*:*:*:*",
                    }]
                }]
            }]
        }
        result = _get_affected(cve)
        assert "apache tomcat 9.0.0" in result[0]

    def test_handles_wildcard_versions(self):
        cve = {
            "configurations": [{
                "nodes": [{
                    "cpeMatch": [{
                        "criteria": "cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*",
                    }]
                }]
            }]
        }
        result = _get_affected(cve)
        assert "apache tomcat" in result[0]
        assert "*" not in result[0]

    def test_deduplicates_results(self):
        cve = {
            "configurations": [{
                "nodes": [{
                    "cpeMatch": [
                        {"criteria": "cpe:2.3:a:apache:tomcat:9.0.0:*:*:*:*:*:*:*"},
                        {"criteria": "cpe:2.3:a:apache:tomcat:9.0.0:*:*:*:*:*:*:*"},
                    ]
                }]
            }]
        }
        result = _get_affected(cve)
        assert len(result) == 1

    def test_limits_to_10_results(self):
        cve = {
            "configurations": [{
                "nodes": [{
                    "cpeMatch": [
                        {"criteria": f"cpe:2.3:a:apache:tomcat:{v}.0.0:*:*:*:*:*:*:*"}
                        for v in range(15)
                    ]
                }]
            }]
        }
        result = _get_affected(cve)
        assert len(result) == 10


class TestBuildIocs:
    def test_returns_specific_iocs_for_cwe89(self):
        iocs = _build_iocs(["CWE-89"])
        assert len(iocs) == 3
        assert any("SQL" in i for i in iocs)

    def test_returns_generic_iocs_for_unknown_cwe(self):
        iocs = _build_iocs(["CWE-9999"])
        assert iocs == [
            "Unexpected outbound network connections from the affected service",
            "Unusual process creation or privilege escalation events",
            "New or modified files in application directories",
            "Spike in error rates or application crashes around the affected component",
        ]

    def test_deduplicates_iocs(self):
        iocs = _build_iocs(["CWE-89", "CWE-89"])
        assert len(iocs) == len(set(iocs))


class TestProcessCve:
    def test_filters_below_min_cvss(self):
        cve = {
            "id": "CVE-2024-1",
            "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 6.5, "baseSeverity": "MEDIUM"}}]},
            "descriptions": [{"lang": "en", "value": "Low severity."}],
            "weaknesses": [],
            "configurations": [],
            "references": [],
            "published": "2024-01-01",
        }
        result = _process_cve(cve)
        assert result is None

    def test_returns_dict_for_high_cvss(self):
        cve = {
            "id": "CVE-2024-2",
            "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}]},
            "descriptions": [{"lang": "en", "value": "RCE vulnerability."}],
            "weaknesses": [{"description": [{"value": "CWE-78"}]}],
            "configurations": [],
            "references": [],
            "published": "2024-01-01",
        }
        result = _process_cve(cve)
        assert result is not None
        assert result["id"] == "CVE-2024-2"
        assert result["score"] == 9.8
        assert "CWE-78" in result["cwes"]
        assert "nvd_url" in result


class TestFetchCvesPaginated:
    def test_handles_empty_results(self):
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = {"vulnerabilities": [], "totalResults": 0}
        with patch("fetch_cves._get_session", return_value=mock_session):
            results = fetch_cves(days_back=1)
        assert results == []

    def test_filters_by_cvss_threshold(self):
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = {
            "vulnerabilities": [
                {"cve": {
                    "id": "CVE-2024-high",
                    "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}]},
                    "descriptions": [{"lang": "en", "value": "High."}],
                    "weaknesses": [],
                    "configurations": [],
                    "references": [],
                    "published": "2024-01-01",
                }},
                {"cve": {
                    "id": "CVE-2024-low",
                    "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 5.0, "baseSeverity": "MEDIUM"}}]},
                    "descriptions": [{"lang": "en", "value": "Low."}],
                    "weaknesses": [],
                    "configurations": [],
                    "references": [],
                    "published": "2024-01-01",
                }},
            ],
            "totalResults": 2,
        }
        with patch("fetch_cves._get_session", return_value=mock_session):
            results = fetch_cves(days_back=1)
        assert len(results) == 1
        assert results[0]["id"] == "CVE-2024-high"

    def test_sorts_by_score_descending(self):
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = {
            "vulnerabilities": [
                {"cve": {
                    "id": "CVE-2024-a",
                    "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 7.5, "baseSeverity": "HIGH"}}]},
                    "descriptions": [{"lang": "en", "value": "A"}],
                    "weaknesses": [], "configurations": [], "references": [], "published": "2024-01-01",
                }},
                {"cve": {
                    "id": "CVE-2024-b",
                    "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.1, "baseSeverity": "CRITICAL"}}]},
                    "descriptions": [{"lang": "en", "value": "B"}],
                    "weaknesses": [], "configurations": [], "references": [], "published": "2024-01-01",
                }},
            ],
            "totalResults": 2,
        }
        with patch("fetch_cves._get_session", return_value=mock_session):
            results = fetch_cves(days_back=1)
        assert results[0]["id"] == "CVE-2024-b"
        assert results[1]["id"] == "CVE-2024-a"


class TestFormatReport:
    def test_format_report_empty(self):
        report = format_report([])
        assert "No CVEs" in report

    def test_format_report_with_cves(self):
        cves = [{
            "id": "CVE-2024-1",
            "score": 9.8,
            "severity": "CRITICAL",
            "description": "RCE vulnerability.",
            "cwes": ["CWE-78"],
            "affected": ["apache tomcat 9.0.0"],
            "references": [{"url": "https://example.com/patch", "tags": ["Patch"]}],
            "iocs": ["Unexpected command execution"],
            "published": "2024-01-01",
            "nvd_url": "https://nvd.nist.gov/vuln/detail/CVE-2024-1",
        }]
        report = format_report(cves, "2024-01-02")
        assert "CVE-2024-1" in report
        assert "CRITICAL" in report
        assert "9.8" in report
        assert "RCE vulnerability" in report
        assert "CWE-78" in report

    def test_format_report_splits_critical_and_high(self):
        cves = [
            {"id": "CVE-C", "score": 9.8, "severity": "CRITICAL", "description": "a", "cwes": [], "affected": [], "references": [], "iocs": [], "published": "2024-01-01", "nvd_url": ""},
            {"id": "CVE-H", "score": 7.5, "severity": "HIGH", "description": "b", "cwes": [], "affected": [], "references": [], "iocs": [], "published": "2024-01-01", "nvd_url": ""},
        ]
        report = format_report(cves, "2024-01-02")
        assert "CRITICAL (9.0-10.0): **1**" in report
        assert "HIGH (7.0-8.9): **1**" in report
