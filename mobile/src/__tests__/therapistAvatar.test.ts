import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockUseAuthenticatedCachedUri } = vi.hoisted(() => ({
  mockUseAuthenticatedCachedUri: vi.fn(),
}))

vi.mock('react', async () => {
  const actual = await vi.importActual<typeof import('react')>('react')
  return {
    ...actual,
    useState: (initial: unknown) => [initial, vi.fn()],
  }
})

vi.mock('react-native', () => ({
  Image: 'Image',
  Text: 'Text',
  View: 'View',
  StyleSheet: {
    create: <T>(styles: T): T => styles,
  },
}))

vi.mock('@/lib/lanHost', () => ({
  rewriteLocalhostToLan: (url: string) => url,
}))

vi.mock('@/api/client', () => ({
  API_BASE_URL: 'https://physiocare-api-6o6j.onrender.com/api/v1',
}))

vi.mock('@/lib/authMedia', () => ({
  useAuthenticatedCachedUri: mockUseAuthenticatedCachedUri,
}))

describe('Mobile TherapistAvatar & media URL resolution', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('resolveMediaUrl builds full URL for relative /media/avatars/ paths', async () => {
    const { resolveMediaUrl } = await import('@/lib/mediaUrl')
    expect(resolveMediaUrl('/media/avatars/therapist-1.jpg')).toBe(
      'https://physiocare-api-6o6j.onrender.com/media/avatars/therapist-1.jpg',
    )
    expect(resolveMediaUrl('')).toBeNull()
    expect(resolveMediaUrl(null)).toBeNull()
  })

  it('TherapistAvatar renders Image when authenticated URI is cached', async () => {
    mockUseAuthenticatedCachedUri.mockReturnValue({
      uri: 'file:///cache/avatar_123.jpg',
      loading: false,
      error: false,
    })

    const { TherapistAvatar } = await import('@/components/TherapistAvatar')
    const element = TherapistAvatar({
      avatarUrl: '/media/avatars/t1.jpg',
      firstName: 'Jan',
      lastName: 'Kowalski',
      size: 48,
    }) as { props: { children: { type: string; props: { source: { uri: string } } } } }

    expect(mockUseAuthenticatedCachedUri).toHaveBeenCalledWith('/media/avatars/t1.jpg')
    expect(element.props.children.type).toBe('Image')
    expect(element.props.children.props.source.uri).toBe('file:///cache/avatar_123.jpg')
  })

  it('TherapistAvatar renders initials fallback when URI fails or is missing', async () => {
    mockUseAuthenticatedCachedUri.mockReturnValue({
      uri: null,
      loading: false,
      error: true,
    })

    const { TherapistAvatar } = await import('@/components/TherapistAvatar')
    const element = TherapistAvatar({
      avatarUrl: '/media/avatars/missing.jpg',
      firstName: 'Jan',
      lastName: 'Kowalski',
      size: 40,
    }) as { props: { children: { type: string; props: { children: string } } } }

    expect(element.props.children.type).toBe('Text')
    expect(element.props.children.props.children).toBe('JK')
  })
})
