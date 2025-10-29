import re
import sys


def install_console_colors() -> None:
    """
    Active un filtre simple qui colorise les balises de log standard
    dans tous les prints de l'application (stdout/stderr), sans modifier
    le code existant. Fonctionne même si colorama est absent.

    Balises reconnues → couleurs:
      [OK]        → vert
      [ERREUR]    → rouge
      [ATTENTION] → jaune
      [INFO]      → cyan
      [SYNC]      → magenta
      [DEBUG]     → gris
      [CALENDRIER]→ bleu
      [IGNORE]    → gris
      [TEST]      → vert clair
    """

    try:
        # Colorama gère les séquences ANSI sous Windows
        from colorama import init as colorama_init, Fore, Style

        colorama_init(autoreset=True)

        tag_to_color = {
            "OK": (Fore.GREEN + Style.BRIGHT, Style.RESET_ALL),
            "ERREUR": (Fore.RED + Style.BRIGHT, Style.RESET_ALL),
            "ATTENTION": (Fore.YELLOW + Style.BRIGHT, Style.RESET_ALL),
            "INFO": (Fore.CYAN, Style.RESET_ALL),
            "SYNC": (Fore.MAGENTA, Style.RESET_ALL),
            "DEBUG": (Fore.WHITE, Style.RESET_ALL),
            "CALENDRIER": (Fore.BLUE, Style.RESET_ALL),
            "IGNORE": (Fore.WHITE, Style.RESET_ALL),
            "TEST": (Fore.GREEN, Style.RESET_ALL),
        }

        tag_regex = re.compile(r"\[(OK|ERREUR|ATTENTION|INFO|SYNC|DEBUG|CALENDRIER|IGNORE|TEST)\]")

        class _ColorizingStream:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def write(self, text):
                try:
                    def _repl(m):
                        tag = m.group(1)
                        start, end = tag_to_color.get(tag, ("", ""))
                        return f"{start}[{tag}]{end}"

                    colored = tag_regex.sub(_repl, text)

                    # Accentuer les lignes d'encadrés "=== ... ==="
                    if colored.startswith("=== ") and colored.rstrip().endswith(" ==="):
                        colored = (Fore.BLUE + Style.BRIGHT) + colored + Style.RESET_ALL

                    self._wrapped.write(colored)
                except Exception:
                    # En cas d'échec, écrire le texte brut
                    self._wrapped.write(text)

            def flush(self):
                try:
                    self._wrapped.flush()
                except Exception:
                    pass

            # Proxy d'attributs (isatty, encoding, etc.)
            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        sys.stdout = _ColorizingStream(sys.stdout)
        sys.stderr = _ColorizingStream(sys.stderr)

    except Exception:
        # Colorama non disponible ou erreur: ne rien faire
        return


