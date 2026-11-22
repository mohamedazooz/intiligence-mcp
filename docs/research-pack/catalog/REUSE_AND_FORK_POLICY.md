# Upstream Reuse, Forking and Code-Incorporation Policy

Open-source code may be reused only after file-level provenance, license and security review. Open source does not mean unrestricted copying.

## Preferred integration order

1. Released package with pinned version and lockfile.
2. Separate service/API with documented contract and isolated credentials.
3. Internal adapter around the dependency or service.
4. Git submodule/subtree pinned to immutable commit where source-level work is needed.
5. Attributed fork with upstream remote and maintained patch series.
6. Small code copy only as a last resort, after exact file license review and notice preservation.

## Prohibited

- Removing copyright, license, NOTICE, attribution or patent notices.
- Copying code with missing, unknown, incompatible or source-available restrictions.
- Mixing AGPL, GPL, enterprise-only or Sustainable Use code into core without explicit legal approval.
- Copying model weights, datasets, templates, signatures, browser binaries or generated assets without checking their separate terms.
- Claiming integration because a repository was cloned or documented.

## Provenance for copied files

Record destination path, upstream repository, immutable commit, upstream file path, SPDX identifier, copyright notice, modifications, reason, reviewer and test reference. Keep THIRD_PARTY_NOTICES and an SPDX or CycloneDX SBOM.

## Fork hygiene

Preserve upstream remote, pin commit, track advisories, keep patches small, test each update and upstream fixes where practical. Never auto-deploy unreviewed upstream changes.

Permissive licenses still require notices. AGPL/GPL and source-available terms require specific review. Mixed licensing must be reviewed per file and edition. Unknown license blocks copying and redistribution. This is engineering guidance, not legal advice.
