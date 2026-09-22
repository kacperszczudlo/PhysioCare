/**
 * @file dataExport.ts
 * @description Funkcje pomocnicze do generowania, zapisywania i udostępniania pliku JSON z pełnym eksportem danych osobowych RODO (Art. 15 / 20 GDPR).
 */

import * as FileSystem from 'expo-file-system'
import { NativeModules, Platform, Share } from 'react-native'

import type { PatientDataExport } from '@/api/types'

/**
 * Wynik operacji udostępnienia lub zapisu pliku eksportu danych pacjenta.
 */
export type DataExportResult =
  | { delivered: true; mode: 'shared' | 'saved'; uri: string; fileName: string }
  | { delivered: false; uri: string; fileName: string }

/** Generuje nazwę pliku eksportu JSON na podstawie daty wykonania zrzutu */
function exportFileName(exportedAt?: string): string {
  const raw = exportedAt?.slice(0, 10)
  const date = raw && /^\d{4}-\d{2}-\d{2}$/.test(raw) ? raw : new Date().toISOString().slice(0, 10)
  return `physiocare-dane-${date}.json`
}

/** Sprawdza, czy moduł natywny ExpoSharing jest zainstalowany i dostępny */
function hasExpoSharingNativeModule(): boolean {
  return Boolean(
    (NativeModules as Record<string, unknown>).ExpoSharing ??
    (NativeModules as Record<string, unknown>).ExpoSharingModule,
  )
}

/** Wywołuje udostępnianie pliku z wykorzystaniem modułu ExpoSharing */
async function shareWithExpoSharing(uri: string): Promise<boolean> {
  if (!hasExpoSharingNativeModule()) {
    return false
  }
  try {
    const Sharing = await import('expo-sharing')
    if (!(await Sharing.isAvailableAsync())) {
      return false
    }
    await Sharing.shareAsync(uri, {
      mimeType: 'application/json',
      dialogTitle: 'Zapisz lub wyślij plik eksportu PhysioCare',
      UTI: 'public.json',
    })
    return true
  } catch {
    return false
  }
}

/** Wywołuje systemowe okno udostępniania pliku w systemie iOS */
async function shareFileOnIos(uri: string): Promise<boolean> {
  try {
    const result = await Share.share({
      url: uri,
      title: 'Eksport danych PhysioCare',
    })
    return result.action !== Share.dismissedAction
  } catch {
    return false
  }
}

/** Zapisuje plik JSON w wybranym folderze urządzenia z wykorzystaniem Storage Access Framework (SAF) na Androidzie */
async function saveJsonViaSaf(
  fileName: string,
  contents: string,
): Promise<{ saved: true; uri: string } | { saved: false }> {
  try {
    const permissions = await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync()
    if (!permissions.granted) {
      return { saved: false }
    }

    const baseName = fileName.replace(/\.json$/i, '')
    const targetUri = await FileSystem.StorageAccessFramework.createFileAsync(
      permissions.directoryUri,
      baseName,
      'application/json',
    )
    await FileSystem.StorageAccessFramework.writeAsStringAsync(targetUri, contents, {
      encoding: 'utf8',
    })
    return { saved: true, uri: targetUri }
  } catch {
    return { saved: false }
  }
}

/**
 * Zapisuje i inicjuje udostępnienie pliku eksportu danych osobowych i medycznych pacjenta w formacie `.json` (zgodnie z wymogami Art. 15 RODO).
 *
 * @param payload - Ładunek danych zwrócony z zapytania `POST /me/data-export/`.
 * @returns Wynik operacji (`DataExportResult`).
 */
export async function sharePatientDataExport(
  payload: PatientDataExport,
): Promise<DataExportResult> {
  const cacheDir = FileSystem.cacheDirectory
  if (!cacheDir) {
    throw new Error('Brak katalogu cache — nie można zapisać eksportu.')
  }

  const fileName = exportFileName(payload.exported_at)
  const contents = JSON.stringify(payload, null, 2)
  const uri = `${cacheDir}${fileName}`
  await FileSystem.writeAsStringAsync(uri, contents, { encoding: 'utf8' })

  if (await shareWithExpoSharing(uri)) {
    return { delivered: true, mode: 'shared', uri, fileName }
  }

  if (Platform.OS === 'ios') {
    const shared = await shareFileOnIos(uri)
    return shared
      ? { delivered: true, mode: 'shared', uri, fileName }
      : { delivered: false, uri, fileName }
  }

  if (Platform.OS === 'android') {
    const result = await saveJsonViaSaf(fileName, contents)
    if (result.saved) {
      return { delivered: true, mode: 'saved', uri: result.uri, fileName }
    }
    return { delivered: false, uri, fileName }
  }

  return { delivered: false, uri, fileName }
}
