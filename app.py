import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import plotly.express as px
import time
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)
st.markdown("""
    <style>
        /* Full-page background with moving clouds */
        .stApp {
            background: linear-gradient(to bottom, #87CEEB 0%, #E0F7FA 60%, #FFFFFF 100%);
            position: relative;
            overflow: hidden;
            min-height: 100vh;
        }

        /* Moving clouds layers */
        .clouds {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }

        .cloud {
            position: absolute;
            background: white;
            border-radius: 50%;
            opacity: 0.7;
            box-shadow: 0 0 40px rgba(255,255,255,0.8);
            animation: drift linear infinite;
        }

        .cloud:nth-child(1) {
            width: 220px;
            height: 80px;
            top: 15%;
            left: -250px;
            animation-duration: 120s;
        }
        .cloud:nth-child(2) {
            width: 180px;
            height: 70px;
            top: 28%;
            left: -300px;
            animation-duration: 140s;
            animation-delay: -30s;
        }
        .cloud:nth-child(3) {
            width: 260px;
            height: 90px;
            top: 45%;
            left: -400px;
            animation-duration: 160s;
            animation-delay: -60s;
        }
        .cloud:nth-child(4) {
            width: 200px;
            height: 75px;
            top: 60%;
            left: -350px;
            animation-duration: 130s;
            animation-delay: -90s;
        }

        @keyframes drift {
            0% { transform: translateX(-100px); }
            100% { transform: translateX(200vw); }
        }

        /* Improve readability on light background */
        h1, h2, h3, p, div, span, label {
            color: #0f172a !important;
            text-shadow: 0 1px 3px rgba(255,255,255,0.8);
        }

        .stMetric-label {
            color: #1e293b !important;
            font-weight: 700;
        }
        .stMetric-value {
            color: #1d4ed8 !important;
            font-weight: bold;
        }

        /* Card-like containers */
        .st-emotion-cache-1r6slb0, .stExpander, .stDataFrame {
            background: rgba(255,255,255,0.88) !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important;
        }

        /* Title enhancement */
        .title-container {
            text-align: center;
            padding: 30px 0 20px;
            color: #1e40af;
        }
    </style>

    <div class="clouds">
        <div class="cloud"></div>
        <div class="cloud"></div>
        <div class="cloud"></div>
        <div class="cloud"></div>
    </div>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=300)
def get_coordinates(city):
    try:
        geolocator = Nominatim(user_agent="weather_dashboard_app")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)
        location = geocode(city)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except:
        return None, None, None

@st.cache_data(show_spinner=False, ttl=300)
def get_weather_data(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
        f"&timezone=auto"
        f"&forecast_days=7"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def map_weather_code(code):
    codes = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
        45: "Fog 🌫️", 51: "Light drizzle 🌧️", 61: "Slight rain 🌧️", 63: "Moderate rain 🌧️",
        71: "Slight snow ❄️", 80: "Rain showers 🌦️", 95: "Thunderstorm ⛈️",
    }
    return codes.get(code, f"Unknown ({code})")

st.markdown('<div class="title-container">', unsafe_allow_html=True)
st.title("🌤️ Weather in a Click")
st.markdown("**Tap a City• Track the Sky• Worldwide**")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("Enter a city to see **current conditions**, **hourly forecast**, and **7-day outlook**")

city_input = st.text_input("City name", placeholder="e.g. Hyderabad, Vijayawada, London, Tokyo", value="Hyderabad")

if city_input.strip():
    with st.spinner("Fetching location and weather data..."):
        lat, lon, full_address = get_coordinates(city_input.strip())
        
        if lat is not None and lon is not None:
            data = get_weather_data(lat, lon)
            
            if data:
                st.success(f"Weather for: **{full_address or city_input}**")
                
                
                current = data["current"]
                cond = map_weather_code(current.get("weather_code", 0))
                
                cols = st.columns([1, 1, 1, 1])
                cols[0].metric("Temperature", f"{current['temperature_2m']} °C", f"Feels like {current['apparent_temperature']} °C")
                cols[1].metric("Humidity", f"{current['relative_humidity_2m']}%")
                cols[2].metric("Wind", f"{current['wind_speed_10m']} km/h")
                cols[3].metric("Rain", f"{current.get('precipitation', 0)} mm")
                
                st.subheader("Condition")
                st.markdown(f"**{cond}** • Updated: {current['time']}")
                
                st.divider()
                
                
                st.subheader("Hourly Forecast (Next 24 Hours)")
                
                hourly = data["hourly"]
                df_hourly = pd.DataFrame({
                    "Time": hourly["time"][:24],
                    "Temperature (°C)": hourly["temperature_2m"][:24],
                    "Humidity (%)": hourly["relative_humidity_2m"][:24],
                    "Rain (mm)": hourly["precipitation"][:24],
                    "Wind (km/h)": hourly["wind_speed_10m"][:24],
                })
                df_hourly["Time"] = pd.to_datetime(df_hourly["Time"])
                
                fig = px.line(df_hourly, x="Time", y="Temperature (°C)", 
                              title="Temperature Trend (Next 24h)", 
                              markers=True,
                              color_discrete_sequence=['#3b82f6'])
                fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Detailed Hourly Table"):
                    st.dataframe(df_hourly.style.format({
                        "Temperature (°C)": "{:.1f}",
                        "Humidity (%)": "{:.0f}",
                        "Rain (mm)": "{:.1f}",
                        "Wind (km/h)": "{:.1f}"
                    }), use_container_width=True)
                
                st.divider()
                
                
                st.subheader("7-Day Forecast")
                
                daily = data["daily"]
                df_daily = pd.DataFrame({
                    "Date": daily["time"],
                    "Condition": [map_weather_code(c) for c in daily["weather_code"]],
                    "Max Temp (°C)": daily["temperature_2m_max"],
                    "Min Temp (°C)": daily["temperature_2m_min"],
                    "Rain Sum (mm)": daily["precipitation_sum"],
                    "Max Wind (km/h)": daily["wind_speed_10m_max"],
                })
                
                st.dataframe(df_daily.style.format({
                    "Max Temp (°C)": "{:.1f}",
                    "Min Temp (°C)": "{:.1f}",
                    "Rain Sum (mm)": "{:.1f}",
                    "Max Wind (km/h)": "{:.1f}"
                }).highlight_max(subset=["Max Temp (°C)"], color="#ffcccc"), 
                use_container_width=True)
                
            else:
                st.error("Could not fetch weather data. Check your internet or try again later.")
        else:
            st.warning("City not found. Try adding country/state, e.g. 'Hyderabad, India'")
else:
    st.info("Enter a city name above to load the dashboard ☝️")

st.markdown("---")
st.caption("Data from Open-Meteo (free API) • Location via Nominatim • Built with Streamlit & Plotly")
