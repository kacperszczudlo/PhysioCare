import type { ReactNode } from 'react'

import { useAuthenticatedMediaUrl } from '@/lib/authMedia'

type AuthMediaImgProps = {
  path: string | null | undefined
  alt?: string
  className?: string
}

export function AuthMediaImg({ path, alt = '', className }: AuthMediaImgProps) {
  const { url } = useAuthenticatedMediaUrl(path)
  if (!url) {
    return null
  }
  return <img src={url} alt={alt} className={className} />
}

type AuthMediaVideoProps = {
  path: string | null | undefined
  className?: string
}

export function AuthMediaVideo({ path, className }: AuthMediaVideoProps) {
  const { url } = useAuthenticatedMediaUrl(path)
  if (!url) {
    return null
  }
  return (
    <video className={className} src={url} controls preload="metadata" playsInline />
  )
}

type AuthMediaPdfLinkProps = {
  path: string | null | undefined
  className?: string
  children: ReactNode
}

export function AuthMediaPdfLink({ path, className, children }: AuthMediaPdfLinkProps) {
  const { url } = useAuthenticatedMediaUrl(path)

  if (!url) {
    return (
      <span className={className} aria-disabled="true">
        {children}
      </span>
    )
  }

  return (
    <a className={className} href={url} target="_blank" rel="noreferrer">
      {children}
    </a>
  )
}
