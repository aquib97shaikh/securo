import React, { createContext, useContext, useState, useEffect } from 'react'

export interface KeyConcept {
  term: string
  definition: string
}

export interface PageInfoSection {
  title: string
  content: string | string[]
  badge?: string
}

export interface PageInfoData {
  title: string
  subtitle: string
  overview?: string
  howToUse?: string[]
  keyConcepts?: KeyConcept[]
  tips: string[]
  shortcuts?: { key: string; description: string }[]
  sections?: PageInfoSection[]
}

interface PageInfoContextValue {
  pageInfo: PageInfoData | null
  setPageInfo: (info: PageInfoData | null) => void
}

const PageInfoContext = createContext<PageInfoContextValue>({
  pageInfo: null,
  setPageInfo: () => {},
})

export function PageInfoProvider({ children }: { children: React.ReactNode }) {
  const [pageInfo, setPageInfo] = useState<PageInfoData | null>(null)

  return (
    <PageInfoContext.Provider value={{ pageInfo, setPageInfo }}>
      {children}
    </PageInfoContext.Provider>
  )
}

export function usePageInfoContext() {
  return useContext(PageInfoContext)
}

/**
 * Hook for any page or sub-view (e.g. MonteCarloView, CalendarView)
 * to publish its specific help, usage instructions, and concepts
 * to the right Info Panel while visible.
 */
export function usePageInfo(info: PageInfoData | null) {
  const { setPageInfo } = usePageInfoContext()
  const serialized = JSON.stringify(info)

  useEffect(() => {
    if (info) {
      setPageInfo(info)
    }
    return () => {
      setPageInfo(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serialized])
}
