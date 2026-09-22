import { useRef, type ChangeEvent } from 'react'
import './FileInput.css'

/** Właściwości komponentu wczytywania pliku (PDF, wideo, dokumentacja medyczna). */
export interface FileInputProps {
  /** Etykieta formularza. */
  label?: string
  /** Dozwolone typy plików (MIME lub rozszerzenia, np. 'application/pdf'). */
  accept?: string
  /** Wybrany plik lub null. */
  file: File | null
  /** Callback zmiany pliku. */
  onChange: (file: File | null) => void
  /** Identyfikator pola. */
  id?: string
  /** Wskazówka pomocnicza. */
  hint?: string
  /** Błąd walidacji pliku. */
  error?: string
  /** Dodatkowa klasa CSS. */
  className?: string
}

/**
 * Komponent wczytywania i przeciągania plików (Dropzone) z podglądem rozmiaru i możliwością usunięcia.
 *
 * @example
 * <FileInput label="Załącz skan RTG" file={file} onChange={setFile} accept="image/*" />
 */
export function FileInput({
  label = 'Plik PDF',
  accept = 'application/pdf,.pdf',
  file,
  onChange,
  id,
  hint,
  error,
  className = '',
}: FileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null
    onChange(selected)
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className={`ui-file-input ${className}`.trim()}>
      {label && (
        <label htmlFor={id} className="ui-field__label">
          {label}
        </label>
      )}

      <div
        className={`ui-file-input__dropzone ${file ? 'ui-file-input__dropzone--has-file' : ''} ${
          error ? 'ui-file-input__dropzone--error' : ''
        }`}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          id={id}
          accept={accept}
          onChange={handleFileChange}
          className="ui-file-input__hidden"
        />

        <div className="ui-file-input__content">
          <svg
            className="ui-file-input__icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="M12 12v6" />
            <path d="m9 15 3-3 3 3" />
          </svg>

          {file ? (
            <div className="ui-file-input__file-info">
              <span className="ui-file-input__filename" title={file.name}>
                {file.name}
              </span>
              <span className="ui-file-input__filesize">{formatFileSize(file.size)}</span>
            </div>
          ) : (
            <div className="ui-file-input__placeholder">
              <span className="ui-file-input__action">Wybierz plik PDF</span>
              <span className="ui-file-input__subtext">kliknij, aby wybrać dokument</span>
            </div>
          )}
        </div>

        {file && (
          <button
            type="button"
            className="ui-file-input__clear-btn"
            onClick={handleClear}
            title="Usuń wybrany plik"
            aria-label="Usuń wybrany plik"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>

      {hint && !error && <span className="ui-field__hint">{hint}</span>}
      {error && <span className="ui-field__error">{error}</span>}
    </div>
  )
}
