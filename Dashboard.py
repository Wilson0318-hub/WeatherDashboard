import requests
import pandas as pd
import streamlit as st

API_KEY="CWA-2D78131F-B85B-40FB-9C0A-24A8526DB355"

st.set_page_config(page_title="台灣即時天氣預報", layout="wide")
st.title("🌦 台灣即時天氣 Dashboard（溫度 / 濕度 / 雨量）")


@st.cache_data(ttl=300)
def get_temp_humidity():
    url=f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA-2D78131F-B85B-40FB-9C0A-24A8526DB355"
    res=requests.get(url,verify=False).json()
    

    locations=res["records"]["Station"]

    data=[]
    for item in locations:
        geo = item["GeoInfo"]
        we = item["WeatherElement"]
        data.append({
            "測站": item["StationName"],
            "縣市": geo["CountyName"],
            "鄉鎮": geo["TownName"],
            "經度": float(geo["Coordinates"][1]["StationLongitude"]),  # WGS84
            "緯度": float(geo["Coordinates"][1]["StationLatitude"]),
            "溫度(°C)": float(we["AirTemperature"]) if we["AirTemperature"] != "-99" else None,
            "濕度(%)": float(we["RelativeHumidity"]) if we["RelativeHumidity"] != "-99" else None,
        })
        

    return pd.DataFrame(data)

def get_rainfall():
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={API_KEY}"
    res = requests.get(url,verify=False).json()

    stations = res["records"]["Station"]

    data = []
    for item in stations:
        rain = item.get("RainfallElement", {})

        # 取值時使用 .get() 避免 KeyError
        past10 = rain.get("Past10Min", {}).get("Precipitation", None)
        past1  = rain.get("Past1Hr", {}).get("Precipitation", None)
        past3  = rain.get("Past3Hr", {}).get("Precipitation", None)
        past24 = rain.get("Past24Hr", {}).get("Precipitation", None)

        data.append({
            "測站": item["StationName"],
            "10分鐘雨量(mm)": float(past10) if past10 not in [None, "-99"] else None,
            "1小時雨量(mm)": float(past1) if past1 not in [None, "-99"] else None,
            "3小時雨量(mm)": float(past3) if past3 not in [None, "-99"] else None,
            "當日累積雨量(mm)": float(past24) if past24 not in [None, "-99"] else None,
        })

    return pd.DataFrame(data)


temp_hum=get_temp_humidity()
rain=get_rainfall()

df=pd.merge(temp_hum,rain,on="測站",how="left")

st.subheader("📊 台灣測站即時天氣總覽")
st.dataframe(df,use_container_width=True)

co1,co2,co3=st.columns(3)

with co1:
    st.metric("🌡️ 全台最高溫", f"{df['溫度(°C)'].max():.1f}°C")

with co2:
    st.metric("💧 全台平均濕度", f"{df['濕度(%)'].mean():.1f}%")

with co3:
    st.metric("🌧 全台最大日累積雨量", f"{df['當日累積雨量(mm)'].max():.1f} mm")

st.success("資料每 5 分鐘自動更新（使用 CWA API O-A0001-001 + O-A0002-001）")

