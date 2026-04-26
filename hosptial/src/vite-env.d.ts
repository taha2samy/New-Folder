/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GRAPH_API_URL: string
  readonly VITE_MANUAL_TEST_TOKEN: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
