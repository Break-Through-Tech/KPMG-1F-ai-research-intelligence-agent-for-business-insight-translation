# Bundled fonts

Variable WOFF2 files (weight and optical-size axes), Latin and Latin Extended subsets, as published
on npm by Fontsource. Both are licensed under the SIL Open Font License 1.1; the licence texts are
in this folder and must ship with the files.

| Family | Package | Files | Licence |
|---|---|---|---|
| Inter | `@fontsource-variable/inter@5.3.0` | `inter-latin(-ext)-opsz-normal.woff2` | `LICENSE-Inter.txt` (OFL 1.1, The Inter Project Authors) |
| Source Serif 4 | `@fontsource-variable/source-serif-4@5.3.1` | `source-serif-4-latin(-ext)-opsz-{normal,italic}.woff2` | `LICENSE-SourceSerif4.txt` (OFL 1.1, Adobe / Google) |

`consult.css` declares them with `@font-face` at `/fonts/…`. They are served by `ui-consult/serve.py`
locally and by `experiments/render-staging/server.py` on the hosted preview (staged by `stage.py`).
