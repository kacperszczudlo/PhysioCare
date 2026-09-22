import pytest
from django.db import connection

from core.crypto import decrypt_value, encrypt_value
from treatment.models import TreatmentEpisode, VisitNote


@pytest.mark.django_db
def test_fernet_crypto_helper_functions() -> None:
    """Sprawdza działanie funkcji pomocniczych szyfrowania i rozszyfrowywania Fernet."""
    # Arrange
    raw_text: str = '44051401359'
    cipher_text: str = encrypt_value(raw_text)

    # Assert
    assert cipher_text != raw_text
    assert cipher_text.startswith('gAAAAA')
    assert decrypt_value(cipher_text) == raw_text

    assert encrypt_value(None) is None
    assert encrypt_value('') == ''
    assert decrypt_value(None) is None
    assert decrypt_value('') == ''


@pytest.mark.django_db
def test_idempotent_encryption_does_not_double_encrypt() -> None:
    """Sprawdza, czy ponowne szyfrowanie już zaszyfrowanego tekstu jest idempotentne."""
    # Arrange
    raw_text: str = 'Notatka medyczna pacjenta'
    cipher_1: str = encrypt_value(raw_text)
    cipher_2: str = encrypt_value(cipher_1)

    # Assert
    assert cipher_1 == cipher_2
    assert decrypt_value(cipher_2) == raw_text


@pytest.mark.django_db
def test_encrypted_fields_db_at_rest_privacy(patient: object) -> None:
    """Sprawdza transparentną dekrypcję w ORM oraz obecność zaszyfrowanego tekstu w surowej bazie danych (Data at Rest)."""
    # Arrange
    pesel_val: str = '44051401359'
    patient.pesel = pesel_val
    patient.save()

    episode: TreatmentEpisode = TreatmentEpisode.objects.create(
        patient=patient,
        functional_diagnosis='Ból odcinka lędźwiowego kręgosłupa L4-L5',
    )

    note_text: str = 'Pacjent zgłasza redukcję bólu z VAS 7 na VAS 3 po zabiegu TENS.'
    visit_note: VisitNote = VisitNote.objects.create(
        episode=episode,
        content=note_text,
    )

    patient.refresh_from_db()
    visit_note.refresh_from_db()
    episode.refresh_from_db()

    # Assert
    assert patient.pesel == pesel_val
    assert visit_note.content == note_text
    assert episode.functional_diagnosis == 'Ból odcinka lędźwiowego kręgosłupa L4-L5'
    # Act

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT pesel FROM patient_profiles WHERE id = %s',
            [str(patient.id)],
        )
        raw_pesel_in_db: str = cursor.fetchone()[0]

        cursor.execute(
            'SELECT content FROM visit_notes WHERE id = %s',
            [str(visit_note.id)],
        )
        raw_note_in_db: str = cursor.fetchone()[0]

        cursor.execute(
            'SELECT functional_diagnosis FROM treatment_episodes WHERE id = %s',
            [str(episode.id)],
        )
        raw_diag_in_db: str = cursor.fetchone()[0]

    assert raw_pesel_in_db != pesel_val
    assert raw_pesel_in_db.startswith('gAAAAA')

    assert raw_note_in_db != note_text
    assert raw_note_in_db.startswith('gAAAAA')

    assert raw_diag_in_db != 'Ból odcinka lędźwiowego kręgosłupa L4-L5'
    assert raw_diag_in_db.startswith('gAAAAA')

