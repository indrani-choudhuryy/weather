from datetime import datetime

import pandas as pd
import streamlit as st

from weather import WeatherError, describe_code, get_weather, search_city

st.set_page_config(page_title="Weather App", page_icon="🌤️", layout="centered")
st.title("🌤️ Weather App")
st.caption("Current conditions and a 7-day forecast, powered by Open-Meteo (no API key needed).")


@st.cache_data(ttl=600, show_spinner=False)
def cached_search(name: str):
    return search_city(name)


@st.cache_data(ttl=600, show_spinner=False)
def cached_weather(lat: float, lon: float, units: str):
    return get_weather(lat, lon, units)


def place_label(p: dict) -> str:
    parts = [p["name"], p["region"], p["country"]]
    return ", ".join(part for part in parts if part)


with st.sidebar:
    st.header("Settings")
    units = st.radio("Units", ["metric", "imperial"], format_func=lambda u: "Celsius / km/h" if u == "metric" else "Fahrenheit / mph")

city = st.text_input("City", placeholder="e.g. Mumbai, London, Tokyo")

if city:
    try:
        places = cached_search(city)
    except WeatherError as err:
        st.error(str(err))
        st.stop()

    if not places:
        st.warning(f"No results for '{city}'. Check the spelling or try a nearby city.")
        st.stop()

    chosen = st.selectbox("Select location", places, format_func=place_label) if len(places) > 1 else places[0]

    try:
        report = cached_weather(chosen["latitude"], chosen["longitude"], units)
    except WeatherError as err:
        st.error(str(err))
        st.stop()

    cur, daily, u = report["current"], report["daily"], report["units"]
    description, emoji = describe_code(cur["weather_code"])

    st.subheader(f"{emoji} {place_label(chosen)}")
    st.write(f"**{description}** · {'Daytime' if cur['is_day'] else 'Night'}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature", f"{cur['temperature']}{u['temp_symbol']}")
    c2.metric("Feels like", f"{cur['feels_like']}{u['temp_symbol']}")
    c3.metric("Humidity", f"{cur['humidity']}%")
    c4.metric("Wind", f"{cur['wind_speed']} {u['wind_symbol']}")

    st.subheader("7-day forecast")
    rows = []
    for d in daily:
        desc, icon = describe_code(d["weather_code"])
        rows.append({
            "Day": datetime.strptime(d["date"], "%Y-%m-%d").strftime("%a, %d %b"),
            "Weather": f"{icon} {desc}",
            f"High ({u['temp_symbol']})": d["temp_max"],
            f"Low ({u['temp_symbol']})": d["temp_min"],
            f"Rain ({u['precip_symbol']})": d["precipitation"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    chart_df = df.set_index("Day")[[f"High ({u['temp_symbol']})", f"Low ({u['temp_symbol']})"]]
    st.line_chart(chart_df)
else:
    st.info("👆 Enter a city name to get started.")
