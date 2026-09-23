type IconProps = { className?: string }

export function IconSearch({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="6.25" />
      <path d="M16.2 16.2 20.5 20.5" />
    </svg>
  )
}

export function IconFrame({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.5 14.2 9.2 20 10.1 15.6 14.2 16.8 20 12 17.1 7.2 20 8.4 14.2 4 10.1 9.8 9.2Z" />
    </svg>
  )
}

export function IconNote({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 4.5h7.5L19 9v10.5H7z" />
      <path d="M14.5 4.5V9H19" />
      <path d="M9.5 13h5M9.5 16h3.5" />
    </svg>
  )
}

export function IconCheck({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6.5 12.5 10 16l7.5-8" />
    </svg>
  )
}

export function IconChevron({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="m8 10 4 4 4-4" />
    </svg>
  )
}

export function IconArrow({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 12h12" />
      <path d="M13 7l5 5-5 5" />
    </svg>
  )
}
