"""Theme configuration for the application."""
from dataclasses import dataclass

@dataclass
class DarkPalette:
    """Dark Theme Colors."""
    # Backgrounds
    BG_PRIMARY: str = "#0F172A"  # Deep Slate
    BG_SECONDARY: str = "#1E293B"  # Slate 800
    BG_TERTIARY: str = "#334155"   # Slate 700
    BG_GRID: str = "#334155"       # Slate 700 (Reusable grid/disabled bg)
    
    # Foreground
    TEXT_PRIMARY: str = "#F1F5F9"  # Slate 100
    TEXT_SECONDARY: str = "#CBD5E1" # Slate 300 (Lighter for better contrast)
    TEXT_MUTED: str = "#94A3B8"    # Slate 400
    TEXT_INVERSE: str = "#0F172A"
    
    # Accents
    PRIMARY: str = "#3B82F6"       # Blue 500
    PRIMARY_LIGHT: str = "#60A5FA" # Blue 400
    PRIMARY_HOVER: str = "#2563EB"
    PRIMARY_PRESSED: str = "#1D4ED8"
    
    SECONDARY: str = "#64748B"     # Slate 500
    SECONDARY_HOVER: str = "#475569"
    
    ACCENT: str = "#F59E0B"        # Amber 500
    ACCENT_HOVER: str = "#D97706"
    DANGER: str = "#EF4444"        # Red 500
    DANGER_HOVER: str = "#DC2626"
    SUCCESS: str = "#10B981"       # Emerald 500
    SUCCESS_HOVER: str = "#059669"
    WARNING: str = "#EAB308"       # Yellow 500
    WARNING_HOVER: str = "#CA8A04" # Yellow 600
    INFO: str = "#3B82F6"          # Blue 500
    INFO_HOVER: str = "#2563EB"    # Blue 600
    
    # Borders
    BORDER: str = "#334155"
    BORDER_FOCUS: str = "#3B82F6"

@dataclass
class LightPalette:
    """Light Theme Colors (Modern Teal - Windows 11 Style)."""
    # Backgrounds
    BG_PRIMARY: str = "#F8FAFC"    # Slate 50 (App Background)
    BG_SECONDARY: str = "#FFFFFF"  # White (Cards, Sidebar)
    BG_TERTIARY: str = "#F1F5F9"   # Slate 100 (Hover, Inputs)
    BG_GRID: str = "#E2E8F0"       # Slate 200
    
    # Foreground
    TEXT_PRIMARY: str = "#0F172A"  # Slate 900
    TEXT_SECONDARY: str = "#475569" # Slate 600 (Darker for better contrast)
    TEXT_MUTED: str = "#64748B"     # Slate 500
    TEXT_INVERSE: str = "#FFFFFF"
    
    # Accents (Modern Teal)
    PRIMARY: str = "#0D9488"       # Teal 600
    PRIMARY_LIGHT: str = "#2DD4BF" # Teal 400
    PRIMARY_HOVER: str = "#0F766E" # Teal 700 (Darker for hover in light mode often works better or keep bright)
    # Actually design specs said: Primary Light #2DD4BF (Hover), Primary Dark #0F766E (Pressed)
    # Let's map standard names:
    PRIMARY: str = "#0D9488"
    PRIMARY_HOVER: str = "#0F766E" # Using Dark for hover to ensure contrast
    PRIMARY_PRESSED: str = "#115E59" # Teal 800
    
    SECONDARY: str = "#64748B"     # Slate 500
    SECONDARY_HOVER: str = "#475569"
    
    ACCENT: str = "#F59E0B"        # Amber 500
    ACCENT_HOVER: str = "#D97706"
    DANGER: str = "#EF4444"        # Red 500
    DANGER_HOVER: str = "#DC2626"
    SUCCESS: str = "#10B981"       # Emerald 500
    SUCCESS_HOVER: str = "#059669"
    WARNING: str = "#EAB308"       # Yellow 500
    WARNING_HOVER: str = "#CA8A04" # Yellow 600
    INFO: str = "#3B82F6"          # Blue 500
    INFO_HOVER: str = "#2563EB"    # Blue 600
    
    # Borders
    BORDER: str = "#E2E8F0"        # Slate 200
    BORDER_FOCUS: str = "#0D9488"  # Primary Teal

class ThemeColors:
    """Proxy class for current theme colors."""
    # Default to Light (Modern Teal)
    _palette = LightPalette()
    
    BG_PRIMARY = _palette.BG_PRIMARY
    BG_SECONDARY = _palette.BG_SECONDARY
    BG_TERTIARY = _palette.BG_TERTIARY
    BG_GRID = _palette.BG_GRID
    
    TEXT_PRIMARY = _palette.TEXT_PRIMARY
    TEXT_SECONDARY = _palette.TEXT_SECONDARY
    TEXT_MUTED = _palette.TEXT_MUTED
    TEXT_INVERSE = _palette.TEXT_INVERSE
    
    PRIMARY = _palette.PRIMARY
    PRIMARY_LIGHT = _palette.PRIMARY_LIGHT
    PRIMARY_HOVER = _palette.PRIMARY_HOVER
    PRIMARY_PRESSED = _palette.PRIMARY_PRESSED
    
    SECONDARY = _palette.SECONDARY
    SECONDARY_HOVER = _palette.SECONDARY_HOVER
    
    ACCENT = _palette.ACCENT
    ACCENT_HOVER = _palette.ACCENT_HOVER
    DANGER = _palette.DANGER
    DANGER_HOVER = _palette.DANGER_HOVER
    SUCCESS = _palette.SUCCESS
    SUCCESS_HOVER = _palette.SUCCESS_HOVER
    WARNING = _palette.WARNING
    WARNING_HOVER = _palette.WARNING_HOVER
    INFO = _palette.INFO
    INFO_HOVER = _palette.INFO_HOVER
    ERROR = DANGER
    ERROR_HOVER = DANGER_HOVER
    
    BORDER = _palette.BORDER
    BORDER_FOCUS = _palette.BORDER_FOCUS

    @classmethod
    def set_theme(cls, mode: str):
        """Set theme mode: 'dark' or 'light'."""
        if mode == "light":
            cls._palette = LightPalette()
        else:
            cls._palette = DarkPalette()
            
        # Update class attributes
        cls.BG_PRIMARY = cls._palette.BG_PRIMARY
        cls.BG_SECONDARY = cls._palette.BG_SECONDARY
        cls.BG_TERTIARY = cls._palette.BG_TERTIARY
        cls.BG_GRID = cls._palette.BG_GRID
        cls.TEXT_PRIMARY = cls._palette.TEXT_PRIMARY
        cls.TEXT_SECONDARY = cls._palette.TEXT_SECONDARY
        cls.TEXT_MUTED = cls._palette.TEXT_MUTED
        cls.TEXT_INVERSE = cls._palette.TEXT_INVERSE
        cls.PRIMARY = cls._palette.PRIMARY
        cls.PRIMARY_LIGHT = cls._palette.PRIMARY_LIGHT
        cls.PRIMARY_HOVER = cls._palette.PRIMARY_HOVER
        cls.PRIMARY_PRESSED = cls._palette.PRIMARY_PRESSED
        cls.SECONDARY = cls._palette.SECONDARY
        cls.SECONDARY_HOVER = cls._palette.SECONDARY_HOVER
        cls.ACCENT = cls._palette.ACCENT
        cls.ACCENT_HOVER = cls._palette.ACCENT_HOVER
        cls.DANGER = cls._palette.DANGER
        cls.DANGER_HOVER = cls._palette.DANGER_HOVER
        cls.SUCCESS = cls._palette.SUCCESS
        cls.SUCCESS_HOVER = cls._palette.SUCCESS_HOVER
        cls.WARNING = cls._palette.WARNING
        cls.WARNING_HOVER = cls._palette.WARNING_HOVER
        cls.INFO = cls._palette.INFO
        cls.INFO_HOVER = cls._palette.INFO_HOVER
        cls.ERROR = cls._palette.DANGER
        cls.ERROR_HOVER = cls._palette.DANGER_HOVER
        cls.BORDER = cls._palette.BORDER
        cls.BORDER_FOCUS = cls._palette.BORDER_FOCUS
        
        # Also need to re-apply the stylesheet in StyleManager after this

class Fonts:
    """Font configurations."""
    HEADER = "24px"
    SUBHEADER = "18px"
    BODY = "14px"
    SMALL = "12px"
    BOLD = "weight: bold"


class ModernTheme:
    """Theme Configuration."""
    
    # Font Settings (Shared)
    FONT_FAMILY = "Segoe UI, Inter, Roboto, sans-serif"
    FONT_SIZE_BASE = "13px"
    FONT_SIZE_LARGE = "16px"
    FONT_SIZE_HEADER = "24px"
    
    @classmethod
    def get_variables(cls):
        """Return a dictionary of variables for QSS replacement."""
        # Use current ThemeColors values
        return {
            "BG_PRIMARY": ThemeColors.BG_PRIMARY,
            "BG_SECONDARY": ThemeColors.BG_SECONDARY,
            "BG_TERTIARY": ThemeColors.BG_TERTIARY,
            "BG_GRID": ThemeColors.BG_GRID,
            
            "TEXT_PRIMARY": ThemeColors.TEXT_PRIMARY,
            "TEXT_SECONDARY": ThemeColors.TEXT_SECONDARY,
            "TEXT_MUTED": ThemeColors.TEXT_MUTED,
            "TEXT_INVERSE": ThemeColors.TEXT_INVERSE,
            
            "PRIMARY": ThemeColors.PRIMARY,
            "PRIMARY_LIGHT": ThemeColors.PRIMARY_LIGHT,
            "PRIMARY_HOVER": ThemeColors.PRIMARY_HOVER,
            "PRIMARY_PRESSED": ThemeColors.PRIMARY_PRESSED,
            
            "SECONDARY": ThemeColors.SECONDARY,
            "SECONDARY_HOVER": ThemeColors.SECONDARY_HOVER,
            
            "DANGER": ThemeColors.DANGER,
            "DANGER_HOVER": ThemeColors.DANGER_HOVER,
            "SUCCESS": ThemeColors.SUCCESS,
            "WARNING": ThemeColors.WARNING,
            "WARNING_HOVER": ThemeColors.WARNING_HOVER,
            "INFO": ThemeColors.INFO,
            "INFO_HOVER": ThemeColors.INFO_HOVER,
            "ACCENT": ThemeColors.ACCENT,
            "ACCENT_HOVER": ThemeColors.ACCENT_HOVER,
            
            "BORDER": ThemeColors.BORDER,
            "BORDER_FOCUS": ThemeColors.BORDER_FOCUS,
            
            "FONT_FAMILY": cls.FONT_FAMILY,
            "FONT_SIZE_BASE": cls.FONT_SIZE_BASE,
            "FONT_SIZE_LARGE": cls.FONT_SIZE_LARGE
        }
