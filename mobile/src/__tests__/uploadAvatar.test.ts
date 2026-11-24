import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockGetAccess, mockRefreshAccessToken, mockUploadAsync, mockCopyAsync, mockDeleteAsync } =
  vi.hoisted(() => ({
    mockGetAccess: vi.fn<() => Promise<string | null>>(),
    mockRefreshAccessToken: vi.fn<() => Promise<boolean>>(),
    mockUploadAsync: vi.fn(),
    mockCopyAsync: vi.fn(),
    mockDeleteAsync: vi.fn(),
  }))

vi.mock('react-native', () => ({
  Platform: { OS: 'android' },
}))

vi.mock('@/lib/lanHost', () => ({
  rewriteLocalhostToLan: (url: string) => url,
}))

vi.mock('@/api/tokenStorage', () => ({
  tokenStorage: {
    getAccess: mockGetAccess,
  },
}))

vi.mock('@/api/client', async () => {
  const actual = await vi.importActual<typeof import('@/api/client')>('@/api/client')
  return {
    ...actual,
    API_BASE_URL: 'https://api.example.com/api/v1',
    refreshAccessToken: mockRefreshAccessToken,
  }
})

vi.mock('expo-file-system/legacy', () => ({
  cacheDirectory: 'file:///data/cache/',
  FileSystemUploadType: { MULTIPART: 1 },
  uploadAsync: mockUploadAsync,
  copyAsync: mockCopyAsync,
  deleteAsync: mockDeleteAsync,
}))

describe('patientApi.uploadAvatar', () => {
  const originalXhr = globalThis.XMLHttpRequest
  const originalFormData = globalThis.FormData

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetAccess.mockResolvedValue('access-token-1')
    mockRefreshAccessToken.mockResolvedValue(false)
    mockCopyAsync.mockResolvedValue(undefined)
    mockDeleteAsync.mockResolvedValue(undefined)
  })

  afterEach(() => {
    globalThis.XMLHttpRequest = originalXhr
    globalThis.FormData = originalFormData
  })

  it('uploads a file:// URI via FileSystem.uploadAsync without copying', async () => {
    const profile = { id: 'p-1', avatar_url: '/media/avatars/new.jpg' }
    mockUploadAsync.mockResolvedValue({
      status: 200,
      body: JSON.stringify(profile),
    })

    const { patientApi } = await import('@/api/patient')
    const result = await patientApi.uploadAvatar('file:///tmp/photo.jpg', 'image/jpeg', 'photo.jpg')

    expect(result).toEqual(profile)
    expect(mockCopyAsync).not.toHaveBeenCalled()
    expect(mockUploadAsync).toHaveBeenCalledWith(
      'https://api.example.com/api/v1/me/profile/avatar/',
      'file:///tmp/photo.jpg',
      expect.objectContaining({
        fieldName: 'file',
        httpMethod: 'POST',
        mimeType: 'image/jpeg',
        headers: {
          Accept: 'application/json',
          Authorization: 'Bearer access-token-1',
        },
      }),
    )
  })

  it('copies a content:// URI to cacheDirectory before upload and cleans it up', async () => {
    const profile = { id: 'p-1', avatar_url: '/media/avatars/content.jpg' }
    mockUploadAsync.mockResolvedValue({
      status: 200,
      body: JSON.stringify(profile),
    })

    const { patientApi } = await import('@/api/patient')
    const result = await patientApi.uploadAvatar(
      'content://media/external/images/media/42',
      'image/png',
      'avatar.png',
    )

    expect(result).toEqual(profile)
    expect(mockCopyAsync).toHaveBeenCalledTimes(1)
    const copyArg = mockCopyAsync.mock.calls[0][0] as { from: string; to: string }
    expect(copyArg.from).toBe('content://media/external/images/media/42')
    expect(copyArg.to).toMatch(/^file:\/\/\/data\/cache\/avatar_upload_\d+_avatar\.png$/)
    expect(mockUploadAsync).toHaveBeenCalledWith(
      'https://api.example.com/api/v1/me/profile/avatar/',
      copyArg.to,
      expect.any(Object),
    )
    expect(mockDeleteAsync).toHaveBeenCalledWith(copyArg.to, { idempotent: true })
  })

  it('refreshes JWT token and retries once when FileSystem.uploadAsync returns 401', async () => {
    const profile = { id: 'p-1', avatar_url: '/media/avatars/refreshed.jpg' }
    mockGetAccess.mockResolvedValueOnce('expired-token').mockResolvedValueOnce('fresh-token')
    mockRefreshAccessToken.mockResolvedValueOnce(true)
    mockUploadAsync
      .mockResolvedValueOnce({ status: 401, body: '{"error":{"message":"Token expired"}}' })
      .mockResolvedValueOnce({ status: 200, body: JSON.stringify(profile) })

    const { patientApi } = await import('@/api/patient')
    const result = await patientApi.uploadAvatar('file:///tmp/photo.jpg')

    expect(result).toEqual(profile)
    expect(mockRefreshAccessToken).toHaveBeenCalledTimes(1)
    expect(mockUploadAsync).toHaveBeenCalledTimes(2)
    expect(mockUploadAsync.mock.calls[1][2].headers.Authorization).toBe('Bearer fresh-token')
  })

  it('falls back to XMLHttpRequest when FileSystem.uploadAsync throws a native error', async () => {
    const profile = { id: 'p-1', avatar_url: '/media/avatars/xhr.jpg' }
    mockUploadAsync.mockRejectedValueOnce(new Error('Native upload failed'))

    class MockFormData {
      append = vi.fn()
    }
    class MockXHR {
      status = 200
      responseText = JSON.stringify(profile)
      timeout = 0
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      ontimeout: (() => void) | null = null
      open = vi.fn()
      setRequestHeader = vi.fn()
      send = vi.fn(() => {
        this.onload?.()
      })
    }
    globalThis.FormData = MockFormData as unknown as typeof FormData
    globalThis.XMLHttpRequest = MockXHR as unknown as typeof XMLHttpRequest

    const { patientApi } = await import('@/api/patient')
    const result = await patientApi.uploadAvatar('file:///tmp/photo.jpg', 'image/jpeg', 'photo.jpg')

    expect(result).toEqual(profile)
  })

  it('refreshes JWT token and retries once in XMLHttpRequest fallback on 401', async () => {
    const profile = { id: 'p-1', avatar_url: '/media/avatars/xhr-refresh.jpg' }
    mockUploadAsync.mockRejectedValueOnce(new Error('Native upload failed'))
    mockGetAccess.mockResolvedValueOnce('expired-token').mockResolvedValueOnce('fresh-token')
    mockRefreshAccessToken.mockResolvedValueOnce(true)

    let attempt = 0
    class MockFormData {
      append = vi.fn()
    }
    class MockXHR {
      status = 0
      responseText = ''
      timeout = 0
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      ontimeout: (() => void) | null = null
      open = vi.fn()
      setRequestHeader = vi.fn()
      send = vi.fn(() => {
        attempt += 1
        if (attempt === 1) {
          this.status = 401
          this.responseText = '{}'
        } else {
          this.status = 200
          this.responseText = JSON.stringify(profile)
        }
        this.onload?.()
      })
    }
    globalThis.FormData = MockFormData as unknown as typeof FormData
    globalThis.XMLHttpRequest = MockXHR as unknown as typeof XMLHttpRequest

    const { patientApi } = await import('@/api/patient')
    const result = await patientApi.uploadAvatar('file:///tmp/photo.jpg')

    expect(result).toEqual(profile)
    expect(attempt).toBe(2)
    expect(mockRefreshAccessToken).toHaveBeenCalledTimes(1)
  })

  it('throws NetworkError when XMLHttpRequest fallback encounters a network failure', async () => {
    mockUploadAsync.mockRejectedValueOnce(new Error('Native upload failed'))

    class MockFormData {
      append = vi.fn()
    }
    class MockXHR {
      timeout = 0
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      ontimeout: (() => void) | null = null
      open = vi.fn()
      setRequestHeader = vi.fn()
      send = vi.fn(() => {
        this.onerror?.()
      })
    }
    globalThis.FormData = MockFormData as unknown as typeof FormData
    globalThis.XMLHttpRequest = MockXHR as unknown as typeof XMLHttpRequest

    const { patientApi } = await import('@/api/patient')
    const { NetworkError } = await import('@/api/client')

    await expect(patientApi.uploadAvatar('file:///tmp/photo.jpg')).rejects.toBeInstanceOf(
      NetworkError,
    )
  })

  it('throws ApiError with server validation message on 400 without falling back', async () => {
    mockUploadAsync.mockResolvedValueOnce({
      status: 400,
      body: JSON.stringify({
        error: { code: 'VALIDATION_ERROR', message: 'Avatar przekracza limit 5 MB.' },
      }),
    })

    const { patientApi } = await import('@/api/patient')
    const { ApiError } = await import('@/api/client')

    await expect(patientApi.uploadAvatar('file:///tmp/huge.jpg')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'Avatar przekracza limit 5 MB.',
    })
    expect(ApiError).toBeDefined()
  })
})
