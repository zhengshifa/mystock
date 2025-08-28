import type { SourceID, SourceResponse } from "@shared/types"
import { getCacheAdapter } from "#/database/adapter"

export default defineEventHandler(async (event) => {
  try {
    const { sources: _ }: { sources: SourceID[] } = await readBody(event)
    const cacheAdapter = await getCacheAdapter()
    const ids = _?.filter(k => sources[k])
    if (ids?.length && cacheAdapter) {
      const caches = await cacheAdapter.getEntire(ids)
      const now = Date.now()
      return caches.map(cache => ({
        status: "cache",
        id: cache.id,
        items: cache.items,
        updatedTime: now - cache.updated < sources[cache.id].interval ? now : cache.updated,
      })) as SourceResponse[]
    }
  } catch {
    //
  }
})
