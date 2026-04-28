"""Data models for AXIS message types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# EEW (緊急地震速報) — channel: "eew"
# ---------------------------------------------------------------------------

@dataclass
class EEWHypocenter:
    Code: int
    Name: str
    Coordinate: List[float]
    Depth: str
    Description: str


@dataclass
class EEWFlag:
    is_final: bool
    is_cancel: bool
    is_training: bool


@dataclass
class EEWForecastIntensity:
    From: str
    To: str
    Description: str


@dataclass
class EEWForecast:
    Code: int
    Name: str
    Intensity: EEWForecastIntensity


@dataclass
class EEWMessage:
    """緊急地震速報メッセージ (channel: eew)"""
    Title: str
    OriginDateTime: str
    ReportDateTime: str
    EventID: str
    Serial: int
    Hypocenter: EEWHypocenter
    Intensity: str
    Magnitude: str
    Flag: EEWFlag
    Forecast: List[EEWForecast]
    Text: str


# ---------------------------------------------------------------------------
# QuakeOne (地震概要・震度情報) — channel: "quake-one"
# ---------------------------------------------------------------------------

@dataclass
class QuakeOneHypocenter:
    Name: str
    Coordinate: List[float]
    Depth: int
    Japanese: str


@dataclass
class QuakeOneInfo:
    EventID: str
    ReportDateTime: str
    OriginDateTime: str
    MaxInt: str
    Magnitude: str
    Hypocenter: QuakeOneHypocenter
    Comments: str


@dataclass
class QuakeOneMessage:
    """地震概要・震度情報メッセージ (channel: quake-one)"""
    headline: str
    info: QuakeOneInfo
    image: str
    largeScalePoints: str
    smallScalePoints: str


# ---------------------------------------------------------------------------
# BreakingNews (ニュース速報) — channel: "breaking-news"
# ---------------------------------------------------------------------------

@dataclass
class BreakingNewsMessage:
    """ニュース速報メッセージ (channel: breaking-news)"""
    Title: str
    Text: List[str]
    ReportDateTime: str


# ---------------------------------------------------------------------------
# JMX Common (気象庁電文共通構造)
# ---------------------------------------------------------------------------

@dataclass
class JMXControl:
    Status: str
    DateTime: str
    PublishingOffice: str
    EditorialOffice: str
    Title: str


@dataclass
class JMXHead:
    EventID: str
    TargetDateTime: str
    InfoType: str
    Title: str
    Headline: Dict[str, Any]
    InfoKindVersion: str
    InfoKind: str
    ReportDateTime: str
    Serial: str


# ---------------------------------------------------------------------------
# JMX Seismology (地震関係) — channel: "jmx-seismology"
# ---------------------------------------------------------------------------

@dataclass
class JMXSeismologyMessage:
    """気象庁地震関係電文メッセージ (channel: jmx-seismology)"""
    Control: JMXControl
    Head: JMXHead
    Body: Dict[str, Any]
    uuid_: str


# ---------------------------------------------------------------------------
# JMX Meteorology (気象情報) — channel: "jmx-meteorology"
# ---------------------------------------------------------------------------

@dataclass
class JMXMeteorologyMessage:
    """気象庁気象情報電文メッセージ (channel: jmx-meteorology)"""
    Control: JMXControl
    Head: JMXHead
    Body: Dict[str, Any]
    uuid_: str


# ---------------------------------------------------------------------------
# JMX Volcanology (火山情報) — channel: "jmx-volcanology"
# ---------------------------------------------------------------------------

@dataclass
class JMXVolcanologyMessage:
    """気象庁火山情報電文メッセージ (channel: jmx-volcanology)"""
    Control: JMXControl
    Head: JMXHead
    Body: Dict[str, Any]
    uuid_: str


# ---------------------------------------------------------------------------
# Raw / Unknown channel fallback
# ---------------------------------------------------------------------------

@dataclass
class RawMessage:
    """パーサーが対応していないチャンネルのメッセージ"""
    channel: str
    data: Dict[str, Any]
