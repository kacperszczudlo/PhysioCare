#!/usr/bin/env python
import os
import sys


def main() -> None:
    """Uruchamia zadania administracyjne CLI Django.

    Raises:
        ImportError: Gdy Django nie jest zainstalowane w środowisku produkcyjnym/wirtualnym.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'physiocare.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
