# Restore testOS

The verified archive must remain untouched:

- Snapshot: `C:\Users\Furkan\Documents\Obsidian\testOS-QA-archives\20260915T010137+0300\snapshot`
- ZIP: `C:\Users\Furkan\Documents\Obsidian\testOS-QA-archives\20260915T010137+0300\testOS-portable.zip`
- ZIP SHA-256: `6cf621c2c731f158973e59d546d38db99c25e39f4a5ae0305ff82522187bb330`

Do not expand over the live vault. Restore to a new sibling directory, verify it, then choose manually whether to switch Obsidian to it.

```powershell
$archive = 'C:\Users\Furkan\Documents\Obsidian\testOS-QA-archives\20260915T010137+0300\testOS-portable.zip'
$restore = 'C:\Users\Furkan\Documents\Obsidian\testOS-restored-20260915'
if (Test-Path -LiteralPath $restore) { throw "Restore target already exists: $restore" }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLower() -ne '6cf621c2c731f158973e59d546d38db99c25e39f4a5ae0305ff82522187bb330') { throw 'Archive hash mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath $restore
Get-ChildItem -LiteralPath $restore -Recurse -File | Measure-Object
```

Expected file count is 419. For an exact restore, compare every restored relative-path SHA-256 with the snapshot manifest in the external archive directory before changing the active Obsidian vault. Do not delete or overwrite `C:\Users\Furkan\Documents\Obsidian\testOS` until the restored copy is independently verified and explicitly selected.
