from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

class TimerWidget(RelativeLayout):
    """
    Widget affichant un timer stylé (bannière arrondie, police et couleurs personnalisables).
    Personnalisation :
        - font_size : taille du texte
        - font_color : couleur du texte
        - banner_color : couleur de fond de la bannière
        - border_color : couleur de la bordure
        - height : hauteur de la bannière
        - label_pos_hint : position du label (pos_hint du Label)
        - banner_width_hint : largeur relative de la bannière
    """
    def __init__(
        self,
        initial_time,
        on_timer_finished=None,
        font_size="22sp",
        font_color=(0.15, 0.08, 0, 1),
        banner_color=(0.98, 0.93, 0.82, 0.92),
        border_color=(0.5, 0.4, 0.2, 0.7),
        height=60,
        label_pos_hint={"center_x": 0.5, "top": 1.1},
        banner_width_hint=0.98,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.remaining_time = max(0, int(initial_time))
        self.on_timer_finished = on_timer_finished

        self.label = Label(
            text="",
            size_hint=(banner_width_hint, None),
            height=height,
            pos_hint=label_pos_hint,
            halign="center",
            valign="middle",
            color=font_color,
            font_size=font_size
        )

        # Bannière arrondie + bordure autour du timer
        with self.label.canvas.before:
            Color(*banner_color)
            self.label_rect = RoundedRectangle(radius=[18], pos=self.label.pos, size=self.label.size)
            Color(*border_color)
            self.label_border = RoundedRectangle(radius=[18], pos=self.label.pos, size=self.label.size, width=2)
        self.label.bind(pos=lambda inst, val: (setattr(self.label_rect, 'pos', val), setattr(self.label_border, 'pos', val)))
        self.label.bind(size=lambda inst, val: (setattr(self.label_rect, 'size', val), setattr(self.label_border, 'size', val)))
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

        self.update_text()
        self.timer_event = None
        if self.remaining_time > 0:
            self.timer_event = Clock.schedule_interval(self._tick, 1)

    def _tick(self, dt):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_text()
        if self.remaining_time <= 0:
            self.update_text()
            if self.timer_event:
                Clock.unschedule(self._tick)
                self.timer_event = None
            if self.on_timer_finished:
                self.on_timer_finished()

    def set_time(self, remaining_time):
        self.remaining_time = max(0, int(remaining_time))
        self.update_text()
        if self.remaining_time > 0 and not self.timer_event:
            self.timer_event = Clock.schedule_interval(self._tick, 1)
        if self.remaining_time <= 0 and self.timer_event:
            Clock.unschedule(self._tick)
            self.timer_event = None

    def update_text(self):
        self.label.text = f"En construction : {self.remaining_time}s" if self.remaining_time > 0 else "Terminé"