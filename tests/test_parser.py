"""Tests for axis.parser module."""

import pytest

from axis.parser import parse_message
from axis.models import (
    BreakingNewsMessage,
    EEWMessage,
    JMXMeteorologyMessage,
    JMXSeismologyMessage,
    JMXVolcanologyMessage,
    QuakeOneMessage,
    RawMessage,
)


# -- EEW ------------------------------------------------------------------

EEW_SAMPLE = {
    "Title": "緊急地震速報（予報）",
    "OriginDateTime": "2022-06-17T00:51:25+09:00",
    "ReportDateTime": "2022-06-17T00:52:19+09:00",
    "EventID": "20220617005133",
    "Serial": 9,
    "Hypocenter": {
        "Code": 601,
        "Name": "徳島県南部",
        "Coordinate": [134.6, 33.9],
        "Depth": "50km",
        "Description": "北緯33.9度 東経134.6度 深さ約50km",
    },
    "Intensity": "4",
    "Magnitude": "5.0",
    "Flag": {"is_final": True, "is_cancel": False, "is_training": False},
    "Forecast": [
        {
            "Code": 610,
            "Name": "香川県東部",
            "Intensity": {
                "From": "4",
                "To": "4",
                "Description": "最大震度4程度",
            },
        }
    ],
    "Text": "",
}


def test_parse_eew():
    msg = parse_message("eew", EEW_SAMPLE)
    assert isinstance(msg, EEWMessage)
    assert msg.Title == "緊急地震速報（予報）"
    assert msg.Magnitude == "5.0"
    assert msg.Hypocenter.Name == "徳島県南部"
    assert msg.Hypocenter.Coordinate == [134.6, 33.9]
    assert msg.Flag.is_final is True
    assert len(msg.Forecast) == 1
    assert msg.Forecast[0].Name == "香川県東部"
    assert msg.Forecast[0].Intensity.From == "4"


# -- QuakeOne ---------------------------------------------------------------

QUAKE_ONE_SAMPLE = {
    "headline": "20日 18時9分頃、宮城県沖を震源とするM7.2の地震がありました。",
    "info": {
        "EventID": "20210320180954",
        "ReportDateTime": "2021-03-20T18:13:00+09:00",
        "OriginDateTime": "2021-03-20T18:09:00+09:00",
        "MaxInt": "5+",
        "Magnitude": "7.2",
        "Hypocenter": {
            "Name": "宮城県沖",
            "Coordinate": [141.7, 38.4],
            "Depth": -60000,
            "Japanese": "北緯３８．４度　東経１４１．７度　深さ　６０ｋｍ",
        },
        "Comments": "津波警報等を発表中です。",
    },
    "image": "http://files.quake.one/20210320180954/image.png",
    "largeScalePoints": "http://files.quake.one/20210320180954/largeScalePoints.json",
    "smallScalePoints": "http://files.quake.one/20210320180954/smallScalePoints.json",
}


def test_parse_quake_one():
    msg = parse_message("quake-one", QUAKE_ONE_SAMPLE)
    assert isinstance(msg, QuakeOneMessage)
    assert msg.info.Magnitude == "7.2"
    assert msg.info.MaxInt == "5+"
    assert msg.info.Hypocenter.Name == "宮城県沖"
    assert msg.info.Hypocenter.Depth == -60000
    assert msg.image.endswith("image.png")


# -- BreakingNews -----------------------------------------------------------

BREAKING_NEWS_SAMPLE = {
    "Title": "NHKニュース速報",
    "Text": [
        "第１６５回直木賞に",
        "佐藤究さんと澤田瞳子さん",
    ],
    "ReportDateTime": "2021-07-14T17:37:05+09:00",
}


def test_parse_breaking_news():
    msg = parse_message("breaking-news", BREAKING_NEWS_SAMPLE)
    assert isinstance(msg, BreakingNewsMessage)
    assert msg.Title == "NHKニュース速報"
    assert len(msg.Text) == 2
    assert msg.ReportDateTime == "2021-07-14T17:37:05+09:00"


# -- JMX Seismology ---------------------------------------------------------

JMX_SEIS_SAMPLE = {
    "Control": {
        "Status": "通常",
        "DateTime": "2021-03-20T09:11:30+00:00",
        "PublishingOffice": "気象庁",
        "EditorialOffice": "気象庁本庁",
        "Title": "震度速報",
    },
    "Head": {
        "EventID": "20210320180954",
        "TargetDateTime": "2021-03-20T18:09:00+09:00",
        "InfoType": "発表",
        "Title": "震度速報",
        "Headline": {"Text": "テスト"},
        "InfoKindVersion": "1.0_1",
        "InfoKind": "震度速報",
        "ReportDateTime": "2021-03-20T18:11:00+09:00",
        "Serial": "",
    },
    "Body": {
        "Intensity": {"Observation": {"MaxInt": "5+"}},
        "Earthquake": [],
    },
    "uuid_": "20210320091132_0_VXSE51_010000",
}


def test_parse_jmx_seismology():
    msg = parse_message("jmx-seismology", JMX_SEIS_SAMPLE)
    assert isinstance(msg, JMXSeismologyMessage)
    assert msg.Control.Title == "震度速報"
    assert msg.Head.EventID == "20210320180954"
    assert msg.Body["Intensity"]["Observation"]["MaxInt"] == "5+"
    assert msg.uuid_ == "20210320091132_0_VXSE51_010000"


# -- JMX Meteorology --------------------------------------------------------

JMX_METE_SAMPLE = {
    "Control": {
        "Status": "通常",
        "DateTime": "2021-03-19T08:13:44+00:00",
        "PublishingOffice": "横浜地方気象台",
        "EditorialOffice": "横浜地方気象台",
        "Title": "府県気象情報",
    },
    "Head": {
        "EventID": "JPTF210010",
        "TargetDateTime": "2021-03-19T17:13:00+09:00",
        "InfoType": "発表",
        "Title": "高波に関する神奈川県気象情報",
        "Headline": {"Text": "テスト", "Information": []},
        "InfoKindVersion": "1.0_0",
        "InfoKind": "同一現象用平文情報",
        "ReportDateTime": "2021-03-19T17:13:00+09:00",
        "Serial": "1",
    },
    "Body": {"MeteorologicalInfos": [], "Comment": {}},
    "uuid_": "20210319081345_0_VPFJ50_140000",
}


def test_parse_jmx_meteorology():
    msg = parse_message("jmx-meteorology", JMX_METE_SAMPLE)
    assert isinstance(msg, JMXMeteorologyMessage)
    assert msg.Control.PublishingOffice == "横浜地方気象台"
    assert msg.Head.InfoKind == "同一現象用平文情報"


# -- JMX Volcanology --------------------------------------------------------

JMX_VOLC_SAMPLE = {
    "Control": {
        "Status": "通常",
        "DateTime": "2021-03-17T18:38:31+00:00",
        "PublishingOffice": "福岡管区気象台　鹿児島地方気象台",
        "EditorialOffice": "福岡管区気象台",
        "Title": "噴火に関する火山観測報",
    },
    "Head": {
        "EventID": "20210318033800_511",
        "TargetDateTime": "2021-03-18T03:28:00+09:00",
        "InfoType": "発表",
        "Title": "火山名　諏訪之瀬島　噴火に関する火山観測報",
        "Headline": {"Text": "噴火テスト"},
        "InfoKindVersion": "1.0_0",
        "InfoKind": "噴火に関する火山観測報",
        "ReportDateTime": "2021-03-18T03:38:00+09:00",
        "Serial": "1",
    },
    "Body": {"VolcanoInfo": [], "VolcanoObservation": {}},
    "uuid_": "20210317183831_0_VFVO53_500000",
}


def test_parse_jmx_volcanology():
    msg = parse_message("jmx-volcanology", JMX_VOLC_SAMPLE)
    assert isinstance(msg, JMXVolcanologyMessage)
    assert msg.Control.Title == "噴火に関する火山観測報"
    assert "諏訪之瀬島" in msg.Head.Title


# -- Unknown channel --------------------------------------------------------

def test_parse_unknown_channel():
    data = {"foo": "bar"}
    msg = parse_message("unknown-channel", data)
    assert isinstance(msg, RawMessage)
    assert msg.channel == "unknown-channel"
    assert msg.data == data
