/**
 * @file httpStatus.ts
 * @description Słownik stałych kodów statusu odpowiedzi HTTP stosowanych w komunikacji z serwerem API.
 */

/**
 * Stałe wartości kodów statusu HTTP.
 */
export const HTTP_STATUS = {
  /** 200 OK - Zapytanie przetworzone pomyślnie */
  OK: 200,
  /** 204 No Content - Operacja powiodła się, brak treści w odpowiedzi */
  NO_CONTENT: 204,
  /** 400 Bad Request - Nieprawidłowe żądanie lub błąd walidacji */
  BAD_REQUEST: 400,
  /** 401 Unauthorized - Wymagana autoryzacja lub nieprawidłowy token */
  UNAUTHORIZED: 401,
  /** 403 Forbidden - Brak wystarczających uprawnień do zasobu */
  FORBIDDEN: 403,
  /** 404 Not Found - Zasób o podanym identyfikatorze nie istnieje */
  NOT_FOUND: 404,
  /** 409 Conflict - Konflikt danych (np. nakładający się termin wizyty) */
  CONFLICT: 409,
  /** 422 Unprocessable Entity - Błąd walidacji strukturalnej danych */
  UNPROCESSABLE_ENTITY: 422,
  /** 500 Internal Server Error - Wewnętrzny błąd serwera */
  INTERNAL_SERVER_ERROR: 500,
} as const
