"""Parse raw AXIS WebSocket messages into typed model objects."""

from __future__ import annotations

from typing import Any, Dict, Union

from .models import (
    BreakingNewsMessage,
    EEWFlag,
    EEWForecast,
    EEWForecastIntensity,
    EEWHypocenter,
    EEWMessage,
    JMXControl,
    JMXHead,
    JMXMeteorologyMessage,
    JMXSeismologyMessage,
    JMXVolcanologyMessage,
    QuakeOneHypocenter,
    QuakeOneInfo,
    QuakeOneMessage,
    RawMessage,
)

MessageType = Union[
    EEWMessage,
    QuakeOneMessage,
    BreakingNewsMessage,
    JMXSeismologyMessage,
    JMXMeteorologyMessage,
    JMXVolcanologyMessage,
    RawMessage,
]


def _parse_eew(msg: Dict[str, Any]) -> EEWMessage:
    hypo = msg["Hypocenter"]
    flag = msg["Flag"]
    forecasts = [
        EEWForecast(
            Code=f["Code"],
            Name=f["Name"],
            Intensity=EEWForecastIntensity(**f["Intensity"]),
        )
        for f in msg.get("Forecast", [])
    ]
    return EEWMessage(
        Title=msg["Title"],
        OriginDateTime=msg["OriginDateTime"],
        ReportDateTime=msg["ReportDateTime"],
        EventID=msg["EventID"],
        Serial=msg["Serial"],
        Hypocenter=EEWHypocenter(**hypo),
        Intensity=msg["Intensity"],
        Magnitude=msg["Magnitude"],
        Flag=EEWFlag(**flag),
        Forecast=forecasts,
        Text=msg.get("Text", ""),
    )


def _parse_quake_one(msg: Dict[str, Any]) -> QuakeOneMessage:
    info = msg["info"]
    hypo = info["Hypocenter"]
    return QuakeOneMessage(
        headline=msg["headline"],
        info=QuakeOneInfo(
            EventID=info["EventID"],
            ReportDateTime=info["ReportDateTime"],
            OriginDateTime=info["OriginDateTime"],
            MaxInt=info["MaxInt"],
            Magnitude=info["Magnitude"],
            Hypocenter=QuakeOneHypocenter(**hypo),
            Comments=info.get("Comments", ""),
        ),
        image=msg.get("image", ""),
        largeScalePoints=msg.get("largeScalePoints", ""),
        smallScalePoints=msg.get("smallScalePoints", ""),
    )


def _parse_breaking_news(msg: Dict[str, Any]) -> BreakingNewsMessage:
    return BreakingNewsMessage(
        Title=msg["Title"],
        Text=msg["Text"],
        ReportDateTime=msg["ReportDateTime"],
    )


def _parse_jmx_control(raw: Dict[str, Any]) -> JMXControl:
    return JMXControl(
        Status=raw["Status"],
        DateTime=raw["DateTime"],
        PublishingOffice=raw["PublishingOffice"],
        EditorialOffice=raw["EditorialOffice"],
        Title=raw["Title"],
    )


def _parse_jmx_head(raw: Dict[str, Any]) -> JMXHead:
    return JMXHead(
        EventID=raw["EventID"],
        TargetDateTime=raw["TargetDateTime"],
        InfoType=raw["InfoType"],
        Title=raw["Title"],
        Headline=raw.get("Headline", {}),
        InfoKindVersion=raw.get("InfoKindVersion", ""),
        InfoKind=raw.get("InfoKind", ""),
        ReportDateTime=raw["ReportDateTime"],
        Serial=raw.get("Serial", ""),
    )


def _parse_jmx_seismology(msg: Dict[str, Any]) -> JMXSeismologyMessage:
    return JMXSeismologyMessage(
        Control=_parse_jmx_control(msg["Control"]),
        Head=_parse_jmx_head(msg["Head"]),
        Body=msg.get("Body", {}),
        uuid_=msg.get("uuid_", ""),
    )


def _parse_jmx_meteorology(msg: Dict[str, Any]) -> JMXMeteorologyMessage:
    return JMXMeteorologyMessage(
        Control=_parse_jmx_control(msg["Control"]),
        Head=_parse_jmx_head(msg["Head"]),
        Body=msg.get("Body", {}),
        uuid_=msg.get("uuid_", ""),
    )


def _parse_jmx_volcanology(msg: Dict[str, Any]) -> JMXVolcanologyMessage:
    return JMXVolcanologyMessage(
        Control=_parse_jmx_control(msg["Control"]),
        Head=_parse_jmx_head(msg["Head"]),
        Body=msg.get("Body", {}),
        uuid_=msg.get("uuid_", ""),
    )


_CHANNEL_PARSERS = {
    "eew": _parse_eew,
    "quake-one": _parse_quake_one,
    "breaking-news": _parse_breaking_news,
    "jmx-seismology": _parse_jmx_seismology,
    "jmx-meteorology": _parse_jmx_meteorology,
    "jmx-volcanology": _parse_jmx_volcanology,
}


def parse_message(channel: str, message: Dict[str, Any]) -> MessageType:
    """Parse a raw message dict into the appropriate typed model.

    Parameters
    ----------
    channel:
        The channel name (e.g. ``"eew"``, ``"quake-one"``).
    message:
        The message payload dict.

    Returns
    -------
    A typed dataclass instance, or :class:`RawMessage` for unknown channels.
    """
    parser = _CHANNEL_PARSERS.get(channel)
    if parser is not None:
        return parser(message)
    return RawMessage(channel=channel, data=message)
