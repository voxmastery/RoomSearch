import { motion, useReducedMotion } from "framer-motion"

export function RoomIllustration() {
  const reduce = useReducedMotion()
  return (
    <motion.div
      className="art-wrap"
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
    >
      <svg className="room-art" viewBox="0 0 480 168" role="img" aria-label="Two agents sharing one room of notes">
        <ellipse cx="240" cy="146" rx="168" ry="10" fill="#EFEBE4" />
        <path d="M96 86C150 18 330 18 384 86" stroke="#E4DFD8" strokeWidth="1" fill="none" />
        <circle cx="168" cy="28" r="2.5" fill="#0E7A5A" />
        <circle cx="240" cy="16" r="2" fill="#0F0F0F" opacity="0.28" />
        <circle cx="312" cy="28" r="2.5" fill="#0F0F0F" opacity="0.18" />

        <rect x="172" y="48" width="156" height="92" rx="18" fill="#EFECE6" />
        <rect x="160" y="36" width="156" height="92" rx="18" fill="#FFFFFF" stroke="#E8E4DE" />
        <rect x="178" y="54" width="68" height="7" rx="3.5" fill="#0F0F0F" />
        <rect x="178" y="70" width="112" height="4" rx="2" fill="#E4DFD8" />
        <rect x="178" y="80" width="92" height="4" rx="2" fill="#E4DFD8" />
        <rect x="178" y="90" width="104" height="4" rx="2" fill="#E4DFD8" />
        <circle cx="292" cy="110" r="7" fill="#E7F6EF" stroke="#0E7A5A" strokeWidth="1.25" />

        <rect x="118" y="46" width="36" height="28" rx="8" fill="#FFFFFF" stroke="#E8E4DE" />
        <rect x="126" y="54" width="16" height="3" rx="1.5" fill="#0F0F0F" />
        <rect x="126" y="61" width="20" height="2" rx="1" fill="#E4DFD8" />

        <rect x="326" y="92" width="36" height="28" rx="8" fill="#FFFFFF" stroke="#C6E6D6" />
        <rect x="334" y="100" width="16" height="3" rx="1.5" fill="#0E7A5A" />
        <rect x="334" y="107" width="20" height="2" rx="1" fill="#E4DFD8" />

        <path d="M92 86H160" stroke="#0F0F0F" strokeWidth="1.25" />
        <path d="M316 86H388" stroke="#0E7A5A" strokeWidth="1.25" />

        <circle cx="64" cy="86" r="28" fill="#0F0F0F" />
        <circle cx="64" cy="86" r="12" stroke="#F7F5F2" strokeWidth="1.4" fill="none" />
        <circle cx="64" cy="86" r="3.5" fill="#E7F6EF" />

        <circle cx="416" cy="86" r="28" fill="#FFFFFF" stroke="#0F0F0F" strokeWidth="1.5" />
        <circle cx="416" cy="86" r="12" stroke="#0E7A5A" strokeWidth="1.4" fill="none" />
        <circle cx="416" cy="86" r="3.5" fill="#0F0F0F" />
      </svg>
    </motion.div>
  )
}

export function MossPulse() {
  return (
    <svg className="glyph moss-glyph" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="6.25" fill="none" stroke="#0E7A5A" strokeOpacity="0.35" />
      <circle cx="8" cy="8" r="3" fill="#0E7A5A" />
    </svg>
  )
}

export function EpisodeSpark() {
  return (
    <svg className="glyph spark" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M8 1.6 9.1 6.4 14 7.4 9.1 8.6 8 13.4 6.9 8.6 2 7.4 6.9 6.4Z" fill="#0E7A5A" />
    </svg>
  )
}
