import type { CollectionAfterChangeHook, GlobalAfterChangeHook } from 'payload'
import { revalidatePath, revalidateTag } from 'next/cache'

/** Clears cached pages after content that appears on many pages changes. */
export const revalidateTagHook =
  (tag: string): CollectionAfterChangeHook & GlobalAfterChangeHook =>
  ({ doc, req }) => {
    if (!req.context?.disableRevalidate) {
      try {
        revalidateTag(tag, 'max')
        revalidatePath('/', 'layout')
      } catch {
        /* outside a Next request (seed / scripts) */
      }
    }
    return doc
  }
