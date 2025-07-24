from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

def make_adaptive_label(text, **kwargs):
    lbl = Label(
        text=text,
        markup=True,
        size_hint_y=None,
        halign=kwargs.get("halign", "left"),
        valign=kwargs.get("valign", "top"),
        **{k: v for k, v in kwargs.items() if k not in ("halign", "valign")}
    )
    lbl.bind(
        width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
        texture_size=lambda instance, value: setattr(instance, 'height', value[1]),
    )
    return lbl

def show_alert_popup(message, title="Erreur"):
    alert = Popup(
        title=title,
        size_hint=(0.5, 0.3),
        auto_dismiss=True
    )
    box = BoxLayout(orientation="vertical", spacing=10, padding=10)
    box.add_widget(make_adaptive_label(f"[color=ff0000]{message}[/color]", halign="center", valign="middle"))
    btn = Button(text="OK", size_hint=(1, None), height=40)
    btn.bind(on_release=lambda instance: alert.dismiss())
    box.add_widget(btn)
    alert.content = box
    alert.open()

def show_confirmation_popup(message, on_confirm, title="Confirmer"):
    popup = Popup(
        title=title,
        size_hint=(0.6, 0.3),
    )
    box = BoxLayout(orientation="vertical", spacing=10, padding=10)
    box.add_widget(Label(
        text=message,
        halign="center", valign="middle"))
    btn_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
    btn_yes = Button(text="Oui", size_hint_x=0.5)
    btn_no = Button(text="Non", size_hint_x=0.5)
    btn_yes.bind(on_press=lambda instance: (on_confirm(instance), popup.dismiss()))
    btn_no.bind(on_press=lambda instance: popup.dismiss())
    btn_box.add_widget(btn_yes)
    btn_box.add_widget(btn_no)
    box.add_widget(btn_box)
    popup.content = box
    popup.open()
