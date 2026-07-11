# Setup guide

## 1. Drop these files into your `anand-esc/anand-esc` repo

```
anand-esc/
├── README.md                       ← replace your current one
├── assets/
│   ├── dark_mode.svg                ← the card (dark)
│   ├── light_mode.svg               ← the card (light)
│   └── today.py                     ← optional: live-stats updater
└── .github/
    └── workflows/
        └── main.yml                 ← optional: runs today.py on a schedule
```

If you just want the **static card** (real photo → ASCII art, your real bio
info, but stats you edit by hand), you only need `README.md` and the two
`assets/*.svg` files. Skip straight to step 4.

## 2. (Optional) Enable live-updating GitHub stats

The `Repos / Stars / Commits / Followers / Lines of Code` row can refresh
itself automatically every 12 hours, the same way Andrew Grant's does.

1. Create a **fine-grained personal access token**:
   `Settings → Developer settings → Personal access tokens → Fine-grained tokens`
   - Repository access: your `anand-esc` repo (and any private repos you want
     counted)
   - Permissions: **Contents: Read and write**, **Metadata: Read-only**
2. Add it as a repo secret: `Settings → Secrets and variables → Actions → New
   repository secret` → name it `ACCESS_TOKEN`, paste the token.
3. That's it — the workflow in `.github/workflows/main.yml` will run
   automatically. You can also trigger it once by hand from the **Actions**
   tab → "Update profile stats" → **Run workflow**, so the numbers populate
   immediately instead of waiting 12 hours.

`today.py` clones each of your repos to count lines of code, so the first
run will take a couple of minutes — that's normal.

## 3. If you skip the automation

Just hand-edit the placeholder numbers directly inside `dark_mode.svg` /
`light_mode.svg` (search for `id="repo_data"`, `id="star_data"`, etc.) — each
one is a plain `<tspan>` with the number as its text content.

## 4. Updating the ASCII art later (new photo, different crop, etc.)

The `tools/` folder has the generator:

```
python3 tools/build_card.py
```

It reads `tools/ascii_final.txt` (the ASCII grid) and rebuilds both SVGs.
To regenerate the art itself from a new photo, open `tools/ascii_gen.py` and
call `make_ascii()` with your image path — tweak `crop_box`, `contrast`,
`gamma`, and `white_cut` until it looks right, save the output, then rerun
`build_card.py`.
