from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty

class NumpadPopup(Popup):
    value = StringProperty("")

    def __init__(self, initial_value="", on_validate=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.6, 0.55)
        self.title = "Clavier numérique"
        self.on_validate = on_validate
        self.value = str(initial_value)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=6, padding=8)
        self.display_input = TextInput(text=self.value, readonly=True, halign='right', font_size=32, size_hint_y=None, height=60)
        layout.add_widget(self.display_input)
        grid = BoxLayout(orientation='vertical', spacing=2)
        rows = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['0', '←', 'OK']
        ]
        for row in rows:
            h = BoxLayout(orientation='horizontal', spacing=2)
            for label in row:
                btn = Button(text=label, font_size=28)
                btn.bind(on_press=self.on_key)
                h.add_widget(btn)
            grid.add_widget(h)
        layout.add_widget(grid)
        self.content = layout

    def on_key(self, instance):
        key = instance.text
        if key.isdigit():
            if self.display_input.text == "0":
                self.display_input.text = key
            else:
                self.display_input.text += key
        elif key == '←':
            self.display_input.text = self.display_input.text[:-1] or "0"
        elif key == 'OK':
            if self.on_validate:
                self.on_validate(self.display_input.text)
            self.dismiss()