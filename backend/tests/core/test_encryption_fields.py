import pytest
from cryptography.fernet import InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings

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


def test_encryption_requires_a_dedicated_key() -> None:
    with override_settings(FIELD_ENCRYPTION_KEY=''):
        from core.crypto import reset_fernet_cache

        reset_fernet_cache()
        with pytest.raises(ImproperlyConfigured):
            encrypt_value('sensitive data')
        reset_fernet_cache()


def test_decryption_does_not_return_invalid_ciphertext_as_plaintext() -> None:
    with pytest.raises(InvalidToken):
        decrypt_value('gAAAAA-invalid-ciphertext')


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


@pytest.mark.django_db
def test_phi_medical_data_fields_encryption_at_rest(patient: object, therapist: object) -> None:
    """Sprawdza, że wrażliwe dane medyczne (F-01) są szyfrowane w bazie danych."""
    from datetime import timedelta

    from django.utils import timezone

    from scheduling.models import TherapyType, Visit
    from treatment.models import BodyAreaPain, TreatmentEpisode

    episode = TreatmentEpisode.objects.create(
        patient=patient,
        summary_note='Poufna notatka podsumowująca stan zdrowia pacjenta.',
    )

    body_pain = BodyAreaPain.objects.create(
        episode=episode,
        body_region='lumbar',
        view_side='BACK',
        vas_score=7,
        pain_character=['ostry', 'kłujący'],
        treatment_targets=['zwiększenie zakresu ruchu'],
    )

    now = timezone.now()

    therapy_type = TherapyType.objects.create(
        therapist=therapist,
        name='Konsultacja fizjoterapeutyczna',
        duration_min=45,
    )
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, hours=1),
        patient_summary='Poufne podsumowanie wizyty pacjenta.',
        patient_note='Pacjent zgłasza ból kolana po urazie.',
        cancel_reason='Pilne skierowanie do chirurga.',
    )

    # 1. Weryfikacja bezpośrednio w bazie (raw SQL)
    with connection.cursor() as cursor:
        cursor.execute('SELECT summary_note FROM treatment_episodes WHERE id = %s', [str(episode.id)])
        db_summary_note = cursor.fetchone()[0]

        cursor.execute(
            'SELECT pain_character, treatment_targets FROM body_area_pain WHERE id = %s',
            [str(body_pain.id)],
        )
        db_pain_char, db_targets = cursor.fetchone()

        cursor.execute(
            'SELECT patient_summary, patient_note, cancel_reason FROM visits WHERE id = %s',
            [str(visit.id)],
        )
        db_visit_summary, db_visit_note, db_cancel_reason = cursor.fetchone()

    assert db_summary_note.startswith('gAAAAA')
    assert 'Poufna notatka' not in db_summary_note

    assert db_pain_char.startswith('gAAAAA')
    assert 'kłujący' not in db_pain_char

    assert db_targets.startswith('gAAAAA')
    assert 'zakresu ruchu' not in db_targets

    assert db_visit_summary.startswith('gAAAAA')
    assert 'Poufne podsumowanie' not in db_visit_summary

    assert db_visit_note.startswith('gAAAAA')
    assert 'ból kolana' not in db_visit_note

    assert db_cancel_reason.startswith('gAAAAA')
    assert 'chirurga' not in db_cancel_reason

    # 2. Weryfikacja transparentnego odczytu przez model Django ORM
    loaded_episode = TreatmentEpisode.objects.get(id=episode.id)
    assert loaded_episode.summary_note == 'Poufna notatka podsumowująca stan zdrowia pacjenta.'

    loaded_pain = BodyAreaPain.objects.get(id=body_pain.id)
    assert loaded_pain.pain_character == ['ostry', 'kłujący']
    assert loaded_pain.treatment_targets == ['zwiększenie zakresu ruchu']

    loaded_visit = Visit.objects.get(id=visit.id)
    assert loaded_visit.patient_summary == 'Poufne podsumowanie wizyty pacjenta.'
    assert loaded_visit.patient_note == 'Pacjent zgłasza ból kolana po urazie.'
    assert loaded_visit.cancel_reason == 'Pilne skierowanie do chirurga.'

