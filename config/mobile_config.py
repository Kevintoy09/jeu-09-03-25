"""
Configuration spécifique pour Android/Mobile
"""
import os
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window

# Détection de la plateforme
IS_MOBILE = platform in ('android', 'ios')
IS_ANDROID = platform == 'android'

# Configuration des dimensions pour mobile
if IS_MOBILE:
    # Configuration pour smartphone
    WINDOW_WIDTH = 360
    WINDOW_HEIGHT = 640
    
    # Tailles adaptées au tactile
    MIN_TOUCH_SIZE = dp(44)  # Taille minimum recommandée pour les boutons tactiles
    BUTTON_HEIGHT = dp(48)
    ICON_SIZE = dp(32)
    FONT_SIZE_NORMAL = dp(16)
    FONT_SIZE_LARGE = dp(20)
    PADDING = dp(8)
    MARGIN = dp(16)
    
else:
    # Configuration pour PC
    WINDOW_WIDTH = 540
    WINDOW_HEIGHT = 960
    
    # Tailles pour desktop
    MIN_TOUCH_SIZE = 32
    BUTTON_HEIGHT = 40
    ICON_SIZE = 24
    FONT_SIZE_NORMAL = 14
    FONT_SIZE_LARGE = 18
    PADDING = 6
    MARGIN = 12

# Gestion des permissions Android
def request_android_permissions():
    """Demande les permissions nécessaires sur Android"""
    if IS_ANDROID:
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        except ImportError:
            # Si les modules Android ne sont pas disponibles (émulateur par exemple)
            pass

# Configuration des gestes tactiles
def configure_touch_settings():
    """Configure les paramètres tactiles pour une meilleure expérience mobile"""
    if IS_MOBILE:
        # Augmenter la zone de détection tactile
        Window.minimum_width = WINDOW_WIDTH
        Window.minimum_height = WINDOW_HEIGHT
        
        # Configuration pour éviter les clics accidentels
        Window.grab_current = True

def get_adaptive_size(base_size):
    """Retourne une taille adaptée à la plateforme"""
    if IS_MOBILE:
        return dp(base_size)
    return base_size

def get_font_size(size_type='normal'):
    """Retourne la taille de police adaptée"""
    sizes = {
        'small': FONT_SIZE_NORMAL * 0.8,
        'normal': FONT_SIZE_NORMAL,
        'large': FONT_SIZE_LARGE,
        'xlarge': FONT_SIZE_LARGE * 1.2
    }
    return sizes.get(size_type, FONT_SIZE_NORMAL)

# Configuration du serveur pour mobile
def get_server_url():
    """Retourne l'URL du serveur adaptée à la plateforme"""
    if IS_ANDROID:
        # Pour Android, utiliser l'IP de votre ordinateur sur le réseau local
        # Vous devrez remplacer cette IP par celle de votre PC
        return "http://192.168.1.100:5000"  # À adapter selon votre réseau
    else:
        return "http://127.0.0.1:5000"

# Gestion du stockage local
def get_storage_path():
    """Retourne le chemin de stockage adapté à la plateforme"""
    if IS_ANDROID:
        try:
            from android.storage import primary_external_storage_path
            return primary_external_storage_path()
        except ImportError:
            return "/sdcard"
    else:
        return os.getcwd()
