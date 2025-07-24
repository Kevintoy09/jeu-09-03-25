# Importer les vues et la classe Navigation
from .header_bar import HeaderBar
from .world_view import WorldView
from .island_view import IslandView
from .city_view import CityView
from .resource_view import ResourceView
from .research_view import ResearchView
from .login_screen import LoginScreen
from .create_account_screen import CreateAccountScreen
from .island_selection_screen import IslandSelectionScreen


# Définir les éléments à exporter par le module views
__all__ = [
    "HeaderBar",
    "WorldView",
    "IslandView",
    "CityView",
    "ResourceView",
    "ResearchView",
    "LoginScreen",
    "CreateAccountScreen",
    "IslandSelectionScreen",
    "Navigation"
]