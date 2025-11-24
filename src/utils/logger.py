"""
Sistema de logging configurável
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from colorama import Fore, Style, init

# Inicializar colorama para Windows
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para diferentes níveis de log"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        # Adicionar cor ao nome do nível
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        
        return super().format(record)


def setup_logger(
    name: str = "jettax_automation",
    log_dir: Optional[Path] = None,
    debug: bool = False,
    console: bool = True
) -> logging.Logger:
    """
    Configura e retorna um logger configurado
    
    Args:
        name: Nome do logger
        log_dir: Diretório para salvar logs
        debug: Se True, nível DEBUG; se False, nível INFO
        console: Se True, também loga no console
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Nível de log
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    # Formato dos logs
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Handler para arquivo
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo com data
        hoje = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"automation_{hoje}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Handler para console
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "jettax_automation") -> logging.Logger:
    """
    Retorna logger existente ou cria um novo
    
    Args:
        name: Nome do logger
    
    Returns:
        Logger
    """
    return logging.getLogger(name)


def configurar_logger(debug: bool = False) -> logging.Logger:
    """
    Configura o logger global do sistema
    
    Args:
        debug: Se True, ativa modo debug
    
    Returns:
        Logger configurado
    """
    # Diretório de logs
    log_dir = Path(__file__).parent.parent.parent / "logs"
    
    # Configurar logger principal
    logger = setup_logger(
        name="jettax_automation",
        log_dir=log_dir,
        debug=debug,
        console=True
    )
    
    return logger
