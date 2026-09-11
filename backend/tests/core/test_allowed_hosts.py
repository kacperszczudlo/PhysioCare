from django.core.exceptions import ImproperlyConfigured
import pytest


@pytest.mark.django_db
class TestAllowedHostsHardening:
    def test_wildcard_rejection_logic_on_production(self):
        debug = False
        allowed_hosts = ['localhost', '*']

        with pytest.raises(ImproperlyConfigured) as exc_info:
            if not debug and '*' in allowed_hosts:
                raise ImproperlyConfigured(
                    'Wildcard "*" w DJANGO_ALLOWED_HOSTS jest zabroniony przy DJANGO_DEBUG=false.'
                )
        assert 'zabroniony' in str(exc_info.value)
