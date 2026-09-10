import * as FileSystem from 'expo-file-system'
import { NativeModules, Platform, Share } from 'react-native'

import type { PatientDataExport } from '@/api/types'

export type DataExportResult =
  | { delivered: true; mode: 'shared' | 'saved'; uri: string; fileName: string }
  | { delivered: false; uri: string; fileName: string }

function exportFileName(exportedAt?: string): string {
  const raw = exportedAt?.slice(0, 10)
  const date =
    raw && /^\d{4}-\d{2}-\d{2}$/.test(raw)
      ? raw
      : new Date().toISOString().slice(0, 10)
  return `physiocare-dane-${date}.json`
}

function hasExpoSharingNativeModule(): boolean {
  return Boolean(
    (NativeModules as Record<string, unknown>).ExpoSharing ??
      (NativeModules as Record<string, unknown>).ExpoSharingModule,
  )
}

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

/** iOS can attach a file:// URL via the built-in Share sheet. */
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

/**
 * Android without expo-sharing: system folder picker + write a real .json file
 * (Downloads / Documents) via Storage Access Framework — already in expo-file-system.
 */
async function saveJsonViaSaf(
  fileName: string,
  contents: string,
): Promise<{ saved: true; uri: string } | { saved: false }> {
  try {
    const permissions =
      await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync()
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
 * Builds a portable RODO export as a real `.json` file (industry default for
 * Art. 15/20 machine-readable access), then lets the user save or send it.
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

  // Web / other: leave file in cache; caller shows soft success.
  return { delivered: false, uri, fileName }
}
