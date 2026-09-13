import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import 'leaflet/dist/leaflet.css'
import './styles/global.css'
import './app-boot.css'

/** OAuth popup returns here with #id_token=… - hand off to opener and close. */
function relayGooglePopupToken(): boolean {
  if (!window.opener || window.opener === window) {
    return false
  }
  const hash = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash
  const search = window.location.search.startsWith('?')
    ? window.location.search.slice(1)
    : window.location.search
  const params = new URLSearchParams(hash || search)
  if (!params.has('id_token') && !params.has('error')) {
    return false
  }
  window.opener.postMessage(
    {
      type: 'physiocare-google-id-token',
      id_token: params.get('id_token') || undefined,
      error: params.get('error') || undefined,
    },
    window.location.origin,
  )
  window.close()
  return true
}

if (!relayGooglePopupToken()) {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
