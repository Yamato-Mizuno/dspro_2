import flet as ft
import requests
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'weather_forecast.db')
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_forecasts (
            area_code TEXT, date TEXT, weather_text TEXT,
            PRIMARY KEY (area_code, date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            code TEXT PRIMARY KEY,
            name TEXT,
            center_name TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_areas_to_db(area_data):
    """取得したエリア情報をDBに保存する"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    area_list = []
    
    centers = area_data.get("centers", {})
    offices = area_data.get("offices", {})
    
    for c_code, c_info in centers.items():
        for o_code in c_info.get("children", []):
            if o_code in offices:
                area_list.append((o_code, offices[o_code]["name"], c_info["name"]))
                
    cur.executemany("INSERT OR REPLACE INTO areas VALUES (?, ?, ?)", area_list)
    conn.commit()
    conn.close()

def get_areas_from_db():
    """DBからエリア情報を取得する"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT code, name, center_name FROM areas ORDER BY center_name")
    rows = cur.fetchall()
    conn.close()
    return rows

def save_forecast_to_db(area_code, times, weathers):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    sql = "INSERT OR REPLACE INTO weather_forecasts VALUES (?, ?, ?);"
    forecast_data = [(area_code, t[:10], w) for t, w in zip(times, weathers)]
    cur.executemany(sql, forecast_data)
    conn.commit()
    conn.close()

def get_forecast_from_db(area_code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT date, weather_text FROM weather_forecasts WHERE area_code = ? ORDER BY date ASC", (area_code,))
    rows = cur.fetchall()
    conn.close()
    return rows

def main(page: ft.Page):
    init_db()
    
    page.title = "お天気予報アプリ (エリアDB版)"
    page.window_width = 1000
    page.window_height = 750
    page.bgcolor = ft.Colors.BLUE_50
    page.padding = 0

    def weather_icon(text: str):
        if "雪" in text: return ft.Icons.AC_UNIT
        if "雨" in text: return ft.Icons.UMBRELLA
        if "晴" in text: return ft.Icons.WB_SUNNY
        return ft.Icons.CLOUD

    weather_list = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[ft.Tab(text="今日"), ft.Tab(text="明日"), ft.Tab(text="明後日")],
        indicator_color=ft.Colors.BLUE_800,
    )

    current_weather = {"times": [], "weathers": []}

    def update_weather_by_tab(tab_index: int):
        weather_list.controls.clear()
        times, weathers = current_weather["times"], current_weather["weathers"]
        if tab_index < len(times):
            weather_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.ListTile(
                            leading=ft.Icon(weather_icon(weathers[tab_index]), color=ft.Colors.BLUE_800, size=40),
                            title=ft.Text(f"{times[tab_index]} の天気", size=20, weight="bold"),
                            subtitle=ft.Text(weathers[tab_index], size=16),
                        )
                    ),
                    color=ft.Colors.WHITE,
                )
            )
        page.update()

    tabs.on_change = lambda e: update_weather_by_tab(e.control.selected_index)

    def show_weather(area_code: str):
        r = requests.get(FORECAST_URL.format(area_code))
        if r.status_code == 200:
            data = r.json()
            ts = data[0]["timeSeries"][0]
            save_forecast_to_db(area_code, ts.get("timeDefines", []), ts.get("areas", [])[0].get("weathers", []))

        db_rows = get_forecast_from_db(area_code)
        current_weather["times"] = [row[0] for row in db_rows]
        current_weather["weathers"] = [row[1] for row in db_rows]
        tabs.selected_index = 0
        update_weather_by_tab(0)

    db_areas = get_areas_from_db()
    if not db_areas:
        area_json = requests.get(AREA_URL).json()
        save_areas_to_db(area_json)
        db_areas = get_areas_from_db()

    left_column = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    current_center = ""
    target_container = None
    
    for code, name, center_name in db_areas:
        if center_name != current_center:
            current_center = center_name
            target_container = ft.ExpansionTile(
                title=ft.Text(center_name, weight="bold", color=ft.Colors.BLUE_800)
            )
            left_column.controls.append(target_container)
        
        target_container.controls.append(
            ft.ListTile(
                title=ft.Text(name, color=ft.Colors.BLUE_900),
                on_click=lambda e, c=code: show_weather(c),
            )
        )

    page.add(
        ft.Container(
            content=ft.Text("天気予報ダッシュボード", color=ft.Colors.WHITE, size=24, weight="bold"),
            bgcolor=ft.Colors.BLUE_800, padding=20, width=page.window_width,
        ),
        ft.Row([
            ft.Container(width=300, bgcolor=ft.Colors.WHITE, content=left_column, padding=10),
            ft.VerticalDivider(width=1),
            ft.Container(expand=True, padding=20, content=ft.Column([tabs, weather_list]))
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)