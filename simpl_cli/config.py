#!/usr/bin/env python3
import os
from pathlib import Path

class Config:

    # Default chat model used when FIREWORKS_MODEL is not provided.
    DEFAULT_API_MODEL = "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new"
    #DEFAULT_API_MODEL = "accounts/fireworks/models/kimi-k2-instruct"
    # Fireworks inference endpoint and timeout shared by all personas.
    API_BASE_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    API_TIMEOUT = 120
    
    ROUTER_ENABLED = True

    # Baseline sampling configuration sent with every completion request.
    AI_CONFIG = {
        "max_tokens": 7000,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6
    }

    # Vector-memory subsystem configuration for conversation recall.
    MEMORY_ENABLED = True
    MEMORY_TOP_K = 5
    MEMORY_EMBEDDING_DIM = 256
    MEMORY_MAX_ITEMS = 500
    MEMORY_PATH = Path.home() / ".cache" / "wrapcli" / "chroma"
    
    # Shell Configuration
    MAX_SHELL_CONTEXT = 10  # Maximum number of shell commands to keep in context
    MAX_CONVERSATION_HISTORY = 20  # Maximum conversation history to keep
    CONTEXT_FOR_AI = 5  # Number of recent commands to send to AI
    
    # Interactive Commands 
    INTERACTIVE_COMMANDS = {
        'nano', 'vim', 'vi', 'emacs', 'mc', 'htop', 'top', 
        'fzf', 'less', 'more', 'man', 'tmux', 'screen',
        'python3', 'python', 'node', 'irb', 'psql', 'mysql',
        'nvim', 'nu', 'xonsh', 'apt', 'sudo',
        'sqlite3', 'redis-cli', 'mongo', 'bash', 'zsh', 'fish'
    }

    # Package-manager commands that should stream live into the terminal UI.
    STREAMING_COMMANDS = {
        'apt', 'apt-get', 'pip', 'pip3', 'npm', 'pnpm', 'yarn',
        'poetry', 'composer', 'cargo', 'brew', 'bundle', 'go', 'apk'
    }

    SHELL_STREAM_SUMMARY_PANEL = True
    SHELL_STREAM_OUTPUT_PANEL = True
    
    # Syntax Highlighting Extensions
    # Map file extensions to syntax lexers for Rich rendering.
    SYNTAX_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript', 
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.xml': 'xml',
        '.md': 'markdown',
        '.txt': 'text'
    }
    
    # Commands that should trigger syntax highlighting
    SYNTAX_HIGHLIGHT_COMMANDS = ['cat', 'head', 'tail', 'batcat', 'bat']

    # Commands treated as directory listings in the output renderer.
    LS_COMMANDS = ['ls', 'la', 'lsd', 'll']

    # File type icons and colors
    FILE_ICONS = {
        'directory': '',  # folder icon
        'file': '',  # file icon
        'executable': '',  # executable icon
        'symlink': '',  # symlink icon
        'image': '',  # image icon
        'video': '󰕧',  # video icon
        'audio': '',  # audio icon
        'archive': '',  # archive icon
        'document': '󰷈',  # document icon
        'code': ' ',  # code icon
    }
    
    FILE_COLORS = {
        'directory': 'bold blue',
        'file': 'white',
        'executable': 'bold green', 
        'symlink': 'cyan',
        'image': 'magenta',
        'video': 'red',
        'audio': 'yellow',
        'archive': 'bold yellow',
        'document': 'blue',
        'code': 'green',
        'hidden': 'dim white'
    }
    
    # File extensions mapping
    FILE_EXTENSIONS = {
        # Images
        '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image', 
        '.bmp': 'image', '.svg': 'image', '.webp': 'image', '.ico': 'image',
        
        # Videos  
        '.mp4': 'video', '.avi': 'video', '.mkv': 'video', '.mov': 'video',
        '.wmv': 'video', '.flv': 'video', '.webm': 'video', '.m4v': 'video',
        
        # Audio
        '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
        '.ogg': 'audio', '.m4a': 'audio', '.wma': 'audio',
        
        # Archives
        '.zip': 'archive', '.rar': 'archive', '.7z': 'archive', '.tar': 'archive',
        '.gz': 'archive', '.bz2': 'archive', '.xz': 'archive', '.deb': 'archive',
        '.rpm': 'archive', '.dmg': 'archive',
        
        # Documents
        '.pdf': 'document', '.doc': 'document', '.docx': 'document', '.xls': 'document',
        '.xlsx': 'document', '.ppt': 'document', '.pptx': 'document', '.txt': 'document',
        '.rtf': 'document', '.odt': 'document', '.ods': 'document', '.odp': 'document',
        
        # Code files
        '.py': 'code', '.js': 'code', '.html': 'code', '.css': 'code', '.java': 'code',
        '.cpp': 'code', '.c': 'code', '.h': 'code', '.php': 'code', '.rb': 'code',
        '.go': 'code', '.rs': 'code', '.swift': 'code', '.kt': 'code', '.scala': 'code',
        '.sh': 'code', '.bash': 'code', '.zsh': 'code', '.fish': 'code', '.json': 'code',
        '.xml': 'code', '.yaml': 'code', '.yml': 'code', '.toml': 'code', '.ini': 'code',
        '.cfg': 'code', '.conf': 'code', '.sql': 'code', '.r': 'code', '.m': 'code'
    }
    
    # UI Configuration
    REFRESH_RATE = 10  # Rich Live refresh rate per second
    
    # Directories
    CONFIG_DIR = Path.home() / '.wrapcli_awokwokw'
    LOG_FILE = CONFIG_DIR / 'shell.log'
    HISTORY_FILE = CONFIG_DIR / 'history.json'
    
    # Prompts and Messages
    WELCOME_MESSAGE = """ [bold]HybridShell ready to launch[/bold]
Alt+H: help • Ctrl+C: exit
Shell wrapper + AI planner with stream resume & bash completion"""
    
    HELP_KEYBINDS = [
        ("Ctrl+A", "Switch to AI mode"),
        ("Ctrl+S", "Switch to Shell mode"), 
        ("Alt+H", "Show this help"),
        ("Alt+C", "Clear context & conversation"),
        ("Ctrl+C", "Exit application")
    ]
    
    HELP_SPECIAL_COMMANDS = [
        ("memory clear", "Shell", "Clear memory and reset conversation"),
        ("context", "AI", "Show current shell context"),
        ("exit", "Both", "Exit the shell")
    ]
    
    # Styling
    PROMPT_STYLES = {
        'left_part': '#c6d0f5',
        'right_part': '#c6d0f5',
        'prompt_padding': '#737994',
        'mode_ai': '#f4b8e4 bold',
        'mode_shell': '#8caaee bold',
        'separator': '#737994',
        'path': '#b5cef8 bold',
        'prompt_symbol': '#f2d5cf bold',
        'clock': '#c6d0f5 bold',
        'status': '#a6d189',
        'prompt_border': '#737994',
        'prompt_os': '#f2d5cf',
        'prompt_folder': '#8caaee bold',
    }

    COMPLETION_STYLES = {
        "completion.menu": "#0a0a0a",
        "scrollbar.background": "bg:#0a7e98 bold",
        "completion-menu.completion": "bg:#0a0a0a fg:#aaaaaa bold",
        "completion-menu.completion fuzzymatch.outside": "#aaaaaa underline",
        "completion-menu.completion fuzzymatch.inside": "fg:#9ece6a bold",
        "completion-menu.completion fuzzymatch.inside.character": "underline bold",
        "completion-menu.completion.current fuzzymatch.outside": "fg:#9ece6a underline",
        "completion-menu.completion.current fuzzymatch.inside": "fg:#f7768e bold",
        "completion-menu.meta.completion": "bg:#0a0a0a fg:#aaaaaa bold",
        "completion-menu.meta.completion.current": "bg:#888888",
    }

    BASH_COMPLETION_FILES = [
        "/usr/share/bash-completion/bash_completion",
        "/etc/bash_completion",
    ]

    BASH_COMPLETION_DIRS = [
        "/usr/share/bash-completion/completions",
        "/etc/bash_completion.d",
    ]

    PANEL_STYLES = {
        "default": {
            "border_style": "#888888",
            "padding": (0, 1),
        },
        "info": {
            "border_style": "#8caaee",
            "padding": (0, 1),
        },
        "success": {
            "border_style": "#a6d189",
            "padding": (0, 1),
        },
        "error": {
            "border_style": "#e78284",
            "padding": (0, 1),
        },
        "warning": {
            "border_style": "#e5c890",
            "padding": (0, 1),
        },
    }
    
    DEFAULT_SHELL = (
        "/bin/bash" if os.name != "nt" else os.environ.get("COMSPEC", "cmd.exe")
    )

    @classmethod
    def ensure_directories(cls):
        cls.CONFIG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_api_key(cls):
        return os.getenv("FIREWORKS_API_KEY")
    
    @classmethod
    def get_model_name(cls):
        return os.getenv("FIREWORKS_MODEL", cls.DEFAULT_API_MODEL)

    @classmethod
    def get_router_model(cls):
        return os.getenv("FIREWORKS_ROUTER_MODEL", cls.get_model_name())

    @classmethod
    def is_router_enabled(cls) -> bool:
        env_value = os.getenv("FIREWORKS_ROUTER_ENABLED")
        if env_value is None:
            return cls.ROUTER_ENABLED

        normalized = env_value.strip().lower()
        return normalized in {"1", "true", "yes", "on"}

    @classmethod
    def get_shell(cls) -> str:
        if os.name == "nt":
            return os.getenv("WRAPCLI_SHELL") or os.getenv("COMSPEC", cls.DEFAULT_SHELL)
        return os.getenv("WRAPCLI_SHELL") or os.getenv("SHELL") or cls.DEFAULT_SHELL

    @classmethod
    def is_shell_stream_summary_enabled(cls) -> bool:
        env_value = os.getenv("WRAPCLI_SHELL_STREAM_PANEL")
        if env_value is None:
            return cls.SHELL_STREAM_SUMMARY_PANEL

        normalized = env_value.strip().lower()
        return normalized in {"1", "true", "yes", "on"}

    @classmethod
    def is_shell_stream_output_panel_enabled(cls) -> bool:
        env_value = os.getenv("WRAPCLI_SHELL_STREAM_OUTPUT_PANEL")
        if env_value is None:
            return cls.SHELL_STREAM_OUTPUT_PANEL

        normalized = env_value.strip().lower()
        return normalized in {"1", "true", "yes", "on"}
