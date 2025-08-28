export {}
declare global {
  const $: typeof import('clsx')['clsx']
  const Author: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/consts')['Author']
  const Homepage: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/consts')['Homepage']
  const Interval: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/consts')['Interval']
  const TTL: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/consts')['TTL']
  const Timer: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index')['Timer']
  const Version: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/consts')['Version']
  const atom: typeof import('jotai')['atom']
  const atomWithStorage: typeof import('jotai/utils')['atomWithStorage']
  const cacheSources: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/data')['cacheSources']
  const columns: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/metadata')['columns']
  const currentColumnIDAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/index')['currentColumnIDAtom']
  const currentSourcesAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/index')['currentSourcesAtom']
  const delay: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/utils')['delay']
  const fixedColumnIds: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/metadata')['fixedColumnIds']
  const focusSourcesAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/index')['focusSourcesAtom']
  const genSources: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/pre-sources')['genSources']
  const goToTopAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/index')['goToTopAtom']
  const hiddenColumns: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/metadata')['hiddenColumns']
  const isPageReload: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useOnReload')['isPageReload']
  const isiOS: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index')['isiOS']
  const metadata: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/metadata')['metadata']
  const myFetch: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index')['myFetch']
  const originSources: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/pre-sources')['originSources']
  const preprocessMetadata: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/primitiveMetadataAtom')['preprocessMetadata']
  const primitiveMetadataAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/primitiveMetadataAtom')['primitiveMetadataAtom']
  const projectDir: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/dir')['projectDir']
  const randomItem: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/utils')['randomItem']
  const randomUUID: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/utils')['randomUUID']
  const refetchSources: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/data')['refetchSources']
  const relativeTime: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/utils')['relativeTime']
  const safeParseString: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index')['safeParseString']
  const sources: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/sources')['default']
  const toastAtom: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useToast')['toastAtom']
  const typeSafeObjectEntries: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/type.util')['typeSafeObjectEntries']
  const typeSafeObjectFromEntries: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/type.util')['typeSafeObjectFromEntries']
  const typeSafeObjectValues: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/type.util')['typeSafeObjectValues']
  const useAtom: typeof import('jotai')['useAtom']
  const useAtomValue: typeof import('jotai')['useAtomValue']
  const useCallback: typeof import('react')['useCallback']
  const useContext: typeof import('react')['useContext']
  const useDark: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useDark')['useDark']
  const useEffect: typeof import('react')['useEffect']
  const useEntireQuery: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/query')['useEntireQuery']
  const useFocus: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useFocus')['useFocus']
  const useFocusWith: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useFocus')['useFocusWith']

  const useMemo: typeof import('react')['useMemo']
  const useOnReload: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useOnReload')['useOnReload']
  const usePWA: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/usePWA')['usePWA']
  const useReducer: typeof import('react')['useReducer']
  const useRef: typeof import('react')['useRef']
  const useRefetch: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useRefetch')['useRefetch']
  const useRelativeTime: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useRelativeTime')['useRelativeTime']
  const useSearchBar: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useSearch')['useSearchBar']
  const useSetAtom: typeof import('jotai')['useSetAtom']
  const useState: typeof import('react')['useState']

  const useToast: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/useToast')['useToast']
  const useUpdateQuery: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/src/hooks/query')['useUpdateQuery']
  const verifyPrimitiveMetadata: typeof import('C:/Users/80441/Desktop/Ashare/newsnow/shared/verify')['verifyPrimitiveMetadata']
}
// for type re-export
declare global {
  // @ts-ignore
  export type { OmitNever, UnionToIntersection, MaybePromise } from 'C:/Users/80441/Desktop/Ashare/newsnow/shared/type.util'
  import('C:/Users/80441/Desktop/Ashare/newsnow/shared/type.util')
  // @ts-ignore
  export type { Color, SourceID, AllSourceID, ColumnID, Metadata, PrimitiveMetadata, FixedColumnID, HiddenColumnID, OriginSource, Source, Column, NewsItem, SourceResponse } from 'C:/Users/80441/Desktop/Ashare/newsnow/shared/types'
  import('C:/Users/80441/Desktop/Ashare/newsnow/shared/types')
  // @ts-ignore
  export type { Timer } from 'C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index'
  import('C:/Users/80441/Desktop/Ashare/newsnow/src/utils/index')
  // @ts-ignore
  export type { Update, ToastItem } from 'C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/types'
  import('C:/Users/80441/Desktop/Ashare/newsnow/src/atoms/types')
}