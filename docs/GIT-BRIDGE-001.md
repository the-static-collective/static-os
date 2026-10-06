# GIT-BRIDGE-001 — explicit Git ingress and egress

Status: candidate user-scoped transport layer stacked above FIRST-PHYSICAL-BOOT-001.

STATIC OS can use Git as a deliberate road between a booted House and project repositories. Git transport does not become OS authority, automatic admission, or a silent self-updater.

```text
FETCH != APPLY
COMMIT != PUSH
PUSH != ADMISSION
SOURCE UPDATE != RUNNING OS UPDATE
REMOTE PERSISTENCE != LOCAL PERSISTENCE
GIT CREDENTIAL != OS AUTHORITY
```

## Surface

The live image includes `git`, `openssh-client`, and the `static-git` command. All managed working trees are constrained beneath `~/static`.

### Inspect without network

```sh
static-git status static-os
```

Reports exact HEAD, branch, origin, dirty state and the last-known upstream relation. It does not contact the network.

### Clone a project

```sh
static-git clone https://github.com/the-static-collective/static-os.git static-os
```

The destination must be a new direct child path under `~/static`. Cloning does not execute project code.

### Fetch without applying

```sh
static-git fetch static-os
```

This runs an explicit `git fetch --prune origin`. It does not alter the checked-out branch or working tree.

### Receive from Git

```sh
static-git receive static-os
```

RECEIVE requires:

- a clean working tree;
- an attached branch;
- an `origin/*` upstream;
- no local/remote divergence.

It fetches and then permits only a fast-forward merge. It never resets, rebases, force-updates, or discards local commits.

For the STATIC OS repository itself, RECEIVE updates the **source checkout only**. The currently booted ISO is immutable for this claim. Applying new OS source means reviewing it and building a new image/boot occurrence.

### Commit selected local work

```sh
static-git commit static-os \
  -m "Record field receipt" \
  --path receipts/first-physical-boot-001.json
```

Every staged path is named explicitly and must stay inside that repository. There is no implicit `git add -A`.

A commit is local. It is not sent automatically.

### Send to Git

```sh
static-git send static-os
```

SEND requires:

- clean captured working state;
- attached branch;
- matching `origin/<branch>` upstream;
- a fresh fetch;
- remote not ahead.

It pushes only the current branch to the matching origin branch.

Credentials are not created, embedded, stored, or copied by STATIC OS. Git uses whatever SSH agent/key or credential helper the human has deliberately configured. HTTP(S) remote URLs containing embedded credentials are refused.

## Persistence boundary

A non-persistent live USB still loses its local `~/static` checkout after reboot.

If a human successfully SENDs a commit to the remote, Git can later reconstruct that project history after another boot. That is **remote repository durability**, not proof of local cross-boot filesystem persistence.

A later POCKET-HOUSE experiment may add removable local persistence under its own gates.
