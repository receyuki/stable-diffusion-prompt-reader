# Development desktop candidate manual check

Record source revision, archive SHA256, target CPU, actual OS, security/quarantine
result and each outcome. This package is a development candidate. Signing,
notarization, oldest OS and physical interactions require separate evidence.

1. Extract to a new location away from source and the build interpreter. Preserve
   the macOS app's permissions/symlinks. Check SHA256SUMS and manifest.json.
2. Start the GUI normally; inspect icons, theme, fonts and image rendering.
3. Use generated PNG/JPEG/WebP samples with spaces, Unicode and braces in paths.
   Open with the native picker, file-manager Open With and physical drag/drop.
   Drop multiple images and check that the first is selected.
4. Resize, switch parameter/raw views, copy prompts/raw text and paste into a
   separate editor. Record actual clipboard contents.
5. Export TXT/JSON; edit and save a copy; reopen and compare prompts, parameters,
   pixel values and transparency. Clear another copy and check both ordinary and
   hidden metadata. Never modify the only source image.
6. Try an unwritable destination and inspect the visible failure. Exercise CLI
   help/read/raw/export/write/clear with redirected output and failure exit codes.
7. Close the window normally, reopen and close again. Record callback errors or
   hanging processes. Repeat on each target OS/CPU before making support claims.

Automated widget invocation does not establish physical picker, drag/drop,
clipboard, file-manager, security-product or oldest-OS behavior. Check validation.json
for the exact automatic checks and limitations of this archive.
