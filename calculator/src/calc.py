import flet as ft
import math

# ...existing code...

class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK


# --- 科学計算モード用の新しいボタンクラス ---
class ScientificButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_700  # 科学計算用として青系の色を使用
        self.color = ft.Colors.WHITE


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()
        self.scientific_mode = False  # 科学計算モードの初期状態

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20

        # --- 科学計算ボタンの行を定義 ---
        self.scientific_row = ft.Row(
            visible=self.scientific_mode,  # 初期状態では非表示
            controls=[
                ScientificButton(text="sin", button_clicked=self.button_clicked),
                ScientificButton(text="cos", button_clicked=self.button_clicked),
                ScientificButton(text="tan", button_clicked=self.button_clicked),
                ScientificButton(text="ln", button_clicked=self.button_clicked),
                ScientificButton(text="log10", button_clicked=self.button_clicked),
                ScientificButton(text="^", button_clicked=self.button_clicked),  # べき乗 (pow)
            ]
        )

        # --- 科学計算モード切替ボタン ---
        self.sci_toggle = ExtraActionButton(text="Sci", button_clicked=self.toggle_scientific_mode)

        # メインのUI構築
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                self.scientific_row,
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        self.sci_toggle,
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    # --- 科学計算モード切り替えメソッド ---
    def toggle_scientific_mode(self, e):
        self.scientific_mode = not self.scientific_mode
        self.scientific_row.visible = self.scientific_mode
        # トグルボタンの色を変更して、モードがアクティブであることを示す
        self.sci_toggle.bgcolor = ft.Colors.BLUE_GREY_100 if not self.scientific_mode else ft.Colors.RED_700
        self.update()

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        current_value = str(self.result.value)

        if current_value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        # --- 数字/小数点 ---
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if current_value == "0" or self.new_operand == True:
                self.result.value = data if data != "." else "0."
                self.new_operand = False
            elif data == "." and "." in current_value:
                pass  # 小数点が既にある場合は何もしない
            else:
                self.result.value = current_value + data

        # --- 通常の二項演算子 ---
        elif data in ("+", "-", "*", "/", "^"):
            try:
                # 前の計算結果をoperand1に格納し、演算子を更新
                self.result.value = self.calculate(self.operand1, float(current_value), self.operator)
                self.operator = data
                if self.result.value == "Error":
                    self.operand1 = 0
                else:
                    self.operand1 = float(self.result.value)
                self.new_operand = True
            except ValueError:
                self.result.value = "Error"
                self.reset()

        # --- 単項演算子・特殊操作 ---
        elif data in ("=", "%", "+/-"):
            try:
                current_num = float(current_value)
                if data == "=":
                    self.result.value = self.calculate(self.operand1, current_num, self.operator)
                    self.reset()
                elif data == "%":
                    self.result.value = self.format_number(current_num / 100)
                    self.reset()
                elif data == "+/-":
                    self.result.value = self.format_number(-current_num)
                    # ACでリセットされることを防ぐため、リセットしない

            except ValueError:
                self.result.value = "Error"
                self.reset()

        # --- 科学計算 (単項演算) ---
        elif data in ("sin", "cos", "tan", "ln", "log10"):
            try:
                current_num = float(current_value)
                if data == "sin":
                    # 入力は度数法として扱う（必要ならラジアンに変更）
                    self.result.value = self.format_number(math.sin(math.radians(current_num)))
                elif data == "cos":
                    self.result.value = self.format_number(math.cos(math.radians(current_num)))
                elif data == "tan":
                    self.result.value = self.format_number(math.tan(math.radians(current_num)))
                elif data == "ln":
                    if current_num <= 0:
                        self.result.value = "Error"
                    else:
                        self.result.value = self.format_number(math.log(current_num))  # 自然対数
                elif data == "log10":
                    if current_num <= 0:
                        self.result.value = "Error"
                    else:
                        self.result.value = self.format_number(math.log10(current_num))

                if self.result.value != "Error":
                    self.operand1 = float(self.result.value)
                self.new_operand = True

            except ValueError:
                self.result.value = "Error"

        self.update()

    def format_number(self, num):
        if abs(num) < 1e-12:
            num = 0.0

        if num % 1 == 0:
            return str(int(num))
        else:
            return f"{num:.10g}".rstrip('0').rstrip('.')

    def calculate(self, operand1, operand2, operator):

        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)

        elif operator == "^":
            try:
                return self.format_number(math.pow(operand1, operand2))
            except (OverflowError, ValueError):
                return "Error"

        return self.format_number(operand2)  # 演算子がない場合はOperand2をそのまま返す

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator"
    # ウィンドウサイズの調整
    page.window_width = 380
    page.window_height = 650
    page.add(CalculatorApp())


ft.app(target=main)

