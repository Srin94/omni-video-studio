# Background music catalog (optional)

Drop royalty-free audio files into the mood subfolders below and the pipeline will
pick a fresh, non-repeating track that matches `payload.suggested_bgm_mood`:

```
assets/music/
  dark_ambient_synth/        # mysteries, true crime, paradoxes
  cinematic_investigative/   # corporate autopsies, heists, history
  upbeat_curious_tech/       # algorithms, how-it-works, science
  acoustic_thoughtful/       # philosophy, economics, human behaviour
```

Supported: `.mp3 .wav .ogg .flac .m4a .aac`.

**If a folder is empty** (or you leave this whole directory empty), the pipeline
synthesizes a fresh procedural ambient bed every render — darker/tenser moods get
lower, more minor voicings — so a video never fails for lack of music and no
audio has to be committed to the repo.

These files are git-ignored by default (see `.gitignore`).
