# render-jobs/

Drop a **render payload JSON** here to render it for free on GitHub Actions.

A payload is the JSON the browser LLM produced for one video (the same thing you
paste into *Validate Schema* in the studio, or feed to
`main.py --payload`). The render workflow re-validates, stamps and backfills it,
so you can commit either the raw model output or an already-validated payload.

## Render one

1. Save your payload as `render-jobs/<name>.json` (the default the workflow
   renders is `render-jobs/payload.json`).
2. Commit and push it.
3. Either let the push trigger the render, or go to **Actions → Render video →
   Run workflow** and point `payload_path` at your file.
4. When it finishes, open the run and download the **`omni-video`** artifact —
   it contains `final_video.mp4` (and the thumbnail).

`format` is read from each payload's own `video_format` (portrait / landscape);
override it with the `format` input on a manual run if you need to.

> `payload.json` here is just a sample — replace it with your own, or add more
> files alongside it. These JSON files carry no secrets (scene text only), so
> they're safe to commit.
