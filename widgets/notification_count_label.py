from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse

class NotificationCountLabel(Widget):
    """
    Badge cercle rouge avec le nombre de notifications non lues.
    Pour mode serveur : le count doit être mis à jour dynamiquement depuis le manager client (qui interroge l'API serveur).
    """
    def __init__(self, count=0, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (26, 26)
        self.count = count
        self.label = Label(
            text=str(count),
            font_size=15,
            bold=True,
            color=(1, 1, 1, 1),
            font_name="Roboto",
            halign="center",
            valign="middle",
            size=self.size,
            size_hint=(None, None),
            pos=self.pos,
        )
        self.add_widget(self.label)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.label.bind(pos=self.update_label_pos, size=self.update_label_pos)
        self.update_graphics()

    def set_count(self, count):
        self.count = count
        self.label.text = str(count)
        self.update_graphics()

    def update_graphics(self, *args):
        self.canvas.before.clear()
        if self.count > 0:
            with self.canvas.before:
                # Contour blanc
                Color(1, 1, 1, 1)
                Ellipse(pos=(self.x-1, self.y-1), size=(self.width+2, self.height+2))
                # Cercle rouge notification
                Color(0.88, 0.07, 0.1, 1)
                Ellipse(pos=self.pos, size=self.size)
        self.update_label_pos()

    def update_label_pos(self, *args):
        self.label.pos = self.pos
        self.label.size = self.size
        self.label.text_size = self.size