---
id: archive-verification
name: Archive Verification in Practice
category: knowledge
tier: B
domain: archives, recovery, integrity
source: field record — archive and NAS recovery work, 2026-08-29 through 2026-09-01
serves: le-sauvegarder
---

# MODULE — Archive Verification in Practice

Knowledge module. It equips Le Sauvegarder — the crown, who preserves — with what went wrong during real verification work, so the next pass does not have to discover it again. Everything below came from an actual incident. Nothing here is general advice that never failed in the field.

Most of it comes down to one rule: **a copy is proven by reading it back, and the reader must be proven too.** Each failure below broke one half of that rule or the other.

## I. Size and mtime prove nothing

**Incident.** A pair of 4 TB archive drives, one made from the other by block-level clone, passed every quick comparison. A full SHA-256 pass then found **1.72 MiB of zero-fill** on the clone where the original held data: 440 pages, each aligned to 4 KiB, spread across three bands of an encrypted sparsebundle.

The damaged files had **identical sizes and identical mtimes, down to the second**, and were fully allocated rather than sparse. `rsync` in default mode, Finder, and every size+mtime comparison reported them in sync, and always would have. Both drives read at full rate with zero kernel I/O errors. The drives were healthy; the clone was at fault. The damage was repaired from the original and re-verified with 0 differing bytes.

**Carried forward.**

- Verify primary archives by checksum only (`shasum -a 256 -c` against a manifest). Treat size+mtime as a way to spot likely changes, never as proof.
- Prefer file-level copies to block clones when making backups. A block clone also copies the volume UUIDs, so two independent drives now share an identity that `diskutil` cannot change.
- Hash with `openssl dgst -sha256`, not `/usr/bin/shasum`. On Apple Silicon the Perl implementation ran ~294 MB/s against ~1.85 GB/s hardware-accelerated, slow enough to become a second bottleneck next to the disk. MD5 has no such hardware path: BSD `md5` and `openssl dgst -md5` both run ~620 MB/s.

**Proportion.** Match the bar to the stakes. A third-copy spare mirror of a source that is already verified may be accepted on existence plus exact size. That is the Operator's decision to make and to record. The checksum-only bar applies to the primary pair and to anything that is the **sole verified copy** of source data that cannot be recovered.

## II. The verifier can lie, and it lies in the most alarming direction

**Incident.** ShadowProtect writes an `.md5` sidecar next to each `.spf` volume image:

```
line 1:  <32-hex md5> *<Filename.spf>\r\n     <- the filename may contain spaces
line 2:  ;<image GUID>;<YYYY/MM/DD>\r\n       <- missing from some sidecars
```

The first draft of the verifier split fields with `awk`. `awk` does not treat `\r` as whitespace, so every filename carried a trailing carriage return, and `System Reserved_VOL-b001.spf` split at the space into `System`. Neither fault shows up under `cat`; only `od -c` reveals them. On a perfectly good archive, that script would have reported **pass 0, fail 0**, with every image skipped as unresolvable.

A verifier that cannot *find* its target reports MISSING, and MISSING looks exactly like real loss. A parse bug that fails closed does not fail safe. It invents a disaster.

**Carried forward.**

- Parse sidecars by stripping prefixes, never by splitting fields:

  ```bash
  line=$(head -1 "$m")
  want=${line%% *}        # hash
  rest=${line#* }         # "*Filename With Spaces.spf"
  file=${rest#\*}
  file=${file%$'\r'}
  ```

- **Dry-run the parse before the hash.** Resolve every filename and hash nothing. A dry run takes seconds; a checksum pass takes hours of disk reads. Only start the pass once every target resolves.
- Inspect any file written on Windows with `od -c` before you trust a line-oriented tool with it.

## III. The shell can lie about success

**Incident.** Three separate traps. Each reported success, and each was caught only because the result was verified after the write.

1. **`cp` aliased to `cp -i`.** When the interactive prompt has no terminal, a scripted copy does nothing and still exits 0.
2. **`rm` aliased to `rm -i`.** A scripted removal printed what looked like a normal deletion, but the file survived. A 128 KiB rsync temp file stayed in a mirror that had already been verified, and turned up in a fresh SHA-256 manifest after an `rm` that claimed it was gone.
3. **LibreSSL is not OpenSSL.** macOS ships LibreSSL, which prints `SHA256(path)= hash`; OpenSSL 3.x prints `SHA2-256(path)= hash`. A parser written for one form corrupted the path field of the other, **while every hash stayed correct**. The manifest looked right and named the wrong files.

**Carried forward.**

- Assume any destructive coreutil may be aliased in an interactive profile. In scripts, call `/bin/cp`, `/bin/rm`, `/bin/mv` directly, or check `alias <cmd>` first.
- A command's own success message is not evidence. The only evidence is re-reading the destination: hash it, list it, or confirm the file is gone.
- Pin the exact output format of any tool whose output you parse, and test the parser against a real line from *this* machine.

## IV. Reading a source must not write to it

**Incident.** A NAS drive from 2014 held ext4 and had been in the `needs_recovery` state since it lost power in the middle of a write. Any normal mount replays the ext4 journal. **Replaying is a write to the recovery source.** A filesystem driver (extFS, macFUSE) also makes macOS treat the volume as writable, and system daemons immediately add `.Spotlight-V100`, `.fseventsd`, and `.Trashes`.

**Carried forward.** Use a *parser*, not a *driver*. `debugfs` from `e2fsprogs` reads the filesystem without mounting it, so the OS never learns the volume exists:

```sh
brew install e2fsprogs      # keg-only: /opt/homebrew/opt/e2fsprogs/sbin/
sudo debugfs -c -R "ls -l /"                        /dev/diskNsM
sudo debugfs -c -R "rdump /dir /dest"               /dev/diskNsM
```

- **Always pass `-c`.** Without it, debugfs reads the bitmap of every block group on open (~29,772 groups on 3.6 TiB), which looks like a hang for many minutes on a USB spinning disk. `-c` skips the bitmaps *and* forces read-only.
- Use the buffered node `/dev/diskNsM`, not `/dev/rdiskNsM`. The raw device rejects unaligned reads, often by quietly returning nothing.
- The tradeoff: debugfs never replays the journal, so transactions still in flight at the moment of the crash are not reflected. Accept that; do not "fix" it with a mount.

## V. Identify devices by signature, never by name

**Incident.** Mount paths depend on the order drives were plugged in, so they change. A recovery record written weeks earlier cited `/dev/rdisk4`, and by the time anyone read it, that node pointed at the archive drive itself. Block clones share volume UUIDs. Model identifiers did not help either: a third drive of the same model was attached, and `diskutil info` gave it the same media name as the archive drive.

**Carried forward.**

- Before any command that names a device node, run `diskutil list` and identify the target by **partition signature**, for example `GUID_partition_scheme` + `Apple_APFS` versus `Linux_RAID` + a data partition.
- Do not trust a partition type GUID either. WD tags ext4 data partitions "Microsoft Basic Data". The real test is the ext magic `0x53EF` at byte offset 1080 of the partition.
- Never copy a device node out of an old record into a new command.
- SMART data cannot be read through a USB bridge on macOS (`smartctl --scan` shows only internal NVMe). Judge drive health from spin-up behaviour, clean superblock reads, and the absence of I/O errors in `log stream`.

## VI. Transferred is not recovered

**Incident.** The 2014 NAS "photo dump" turned out to be Windows whole-volume images, not a photo folder. It took 6 h to extract and 69 min to verify, and all five completed images matched their 2014 sidecars bit for bit. The recovery was still only proven **transferred**. The photos are inside images that nothing had opened yet, and six unfinished image fragments totalling 1.2 TB never got a sidecar, so no checksum can ever prove them.

**Carried forward.**

- Say which stage is proven: *read*, *transferred*, *verified against source*, *opened*, or *content confirmed*. Each stage is a separate claim.
- Data with no checksum can only be re-verified against a fresh read of its source. **Its source stays load-bearing.** Do not format or reuse it until the content is confirmed present.

## DOCTRINE — Mapping To The Instrument

- **Le Sauvegarder** holds the bar: checksum-only for primary and sole copies, and the Operator decides the bar for redundant copies.
- **Le Sceptique** carries section III into every turn. A tool's success message is a claim, and a claim is not verified until the result has been read back. This is the same discipline as Le Rouage's `(unverified)` rule.
- **Le Vigile** carries section IV: a read from a source must be structurally unable to write to it, not merely careful about it.
- **Le Limier** carries section V: an identity comes from a signature, and a name alone is only a lead.

A thing documented is a thing not yet lost.
