# RuinedFooocus regression tests

`issue77.png` is the unchanged PNG attached by almfisch to
[issue #77](https://github.com/receyuki/stable-diffusion-prompt-reader/issues/77)
on 2024-06-14. Original attachment:
https://github.com/receyuki/stable-diffusion-prompt-reader/assets/7447539/ae719ebf-8c02-4175-ba16-14523200805e

The expected model, sampler, seed, CFG, steps and dimensions were checked against
the PNG's `parameters` JSON. Prompt and extra-field assertions compare with the
original metadata directly, not with parser-generated snapshots.

Tests read the original image without modifying it. Boundary cases use synthetic
in-memory PNGs with variations of its metadata. No network access is required.
This fixture records a user-provided sample; it does not establish permission to
redistribute the image under the project's MIT license.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -q -p no:cacheprovider tests/ruinedfooocus
```

Coverage: original PNG fields, raw/settings preservation, A1111 false-positive
avoidance, optional missing/null fields, image-size fallback, zero values,
invalid prompt types and malformed JSON. Only the supplied PNG metadata layout
is verified; this does not establish JPEG/WebP or all-version compatibility.
