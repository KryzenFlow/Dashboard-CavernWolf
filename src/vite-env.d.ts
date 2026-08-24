/// <reference types="vite/client" />

declare module "*.css";

interface ImportMetaEnv {
  readonly VITE_HERMES_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
