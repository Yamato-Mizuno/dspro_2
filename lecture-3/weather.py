import flet as ft
import requests

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


def main(page: ft.Page):
    page.title = "気象庁 天気予報アプリ"
    page.window_width = 1000
    page.window_height = 600
    page.bgcolor = ft.Colors.WHITE

#天気のアイコンを指定する関数
    def weather_icon(text: str):
        if "雪" in text:
            return ft.Icons.AC_UNIT
        if "雨" in text:
            return ft.Icons.UMBRELLA
        if "晴" in text:
            return ft.Icons.WB_SUNNY
        if "くもり" in text:
            return ft.Icons.CLOUD
        return ft.Icons.CLOUD

#タグリストの作成
    weather_list = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="今日"),
            ft.Tab(text="明日"),
            ft.Tab(text="明後日"),
        ],
    )

    current_weather = {
        "times": [],
        "weathers": []
    }

    def update_weather_by_tab(tab_index: int):
        weather_list.controls.clear()

        times = current_weather["times"]
        weathers = current_weather["weathers"]

        if tab_index >= len(times):
            weather_list.controls.append(
                ft.Text("天気情報がありません", color=ft.Colors.BLACK)
            )
            page.update()
            return

        weather_list.controls.append(
            ft.ListTile(
                leading=ft.Icon(
                    weather_icon(weathers[tab_index]),
                    color=ft.Colors.BLACK
                ),
                title=ft.Text(times[tab_index][:10], color=ft.Colors.BLACK),
                subtitle=ft.Text(weathers[tab_index], color=ft.Colors.BLACK),
            )
        )

        page.update()

    tabs.on_change = lambda e: update_weather_by_tab(e.control.selected_index)

#データの取得
    def show_weather(area_code: str):
        weather_list.controls.clear()

        url = FORECAST_URL.format(area_code)
        r = requests.get(url)

        if r.status_code != 200:
            weather_list.controls.append(
                ft.Text("天気データを取得できません", color=ft.Colors.RED)
            )
            page.update()
            return

        try:
            data = r.json()
        except ValueError:
            weather_list.controls.append(
                ft.Text("JSONの解析に失敗しました", color=ft.Colors.RED)
            )
            page.update()
            return

        ts = data[0]["timeSeries"][0]
        current_weather["times"] = ts.get("timeDefines", [])
        current_weather["weathers"] = ts.get("areas", [])[0].get("weathers", [])

        tabs.selected_index = 0
        update_weather_by_tab(0)

    # 地域データ取得
    area_json = requests.get(AREA_URL).json()
    centers = area_json["centers"]
    offices = area_json["offices"]

    left_column = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=5
    )

    left_column.controls.append(
        ft.Text(
            "地域を選択",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLACK
        )
    )

    for center in centers.values():
        prefecture_tiles = []

        for office_code in center["children"]:
            prefecture_tiles.append(
                ft.ListTile(
                    title=ft.Text(
                        offices[office_code]["name"],
                        color=ft.Colors.BLACK
                    ),
                    subtitle=ft.Text(
                        office_code,
                        size=11,
                        color=ft.Colors.GREY
                    ),
                    on_click=lambda e, c=office_code: show_weather(c)
                )
            )

        left_column.controls.append(
            ft.ExpansionTile(
                title=ft.Text(
                    center["name"],
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK
                ),
                controls=prefecture_tiles,
                text_color=ft.Colors.BLACK,
                collapsed_text_color=ft.Colors.BLACK,
                icon_color=ft.Colors.BLACK,
                collapsed_icon_color=ft.Colors.BLACK,
            )
        )

    page.add(
        ft.Row(
            [
                ft.Container(
                    width=300,
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    content=left_column
                ),
                ft.VerticalDivider(width=1),
                ft.Column(
                    expand=True,
                    controls=[
                        tabs,
                        weather_list
                    ]
                )
            ],
            expand=True
        )
    )


ft.app(target=main)
