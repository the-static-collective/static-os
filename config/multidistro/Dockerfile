# GENESIS-BOOT-004: two non-Debian Linux userlands running the ORIGINAL
# 11 independently versioned source histories. This is an OCI build, NOT ISO.
# Base tags are mutable and will be reported as resolved digests by CI.
ARG BASE_IMAGE=node:24-alpine
FROM ${BASE_IMAGE}
ARG TARGET_DISTRO=alpine
SHELL ["/bin/sh", "-ec"]
RUN if [ "${TARGET_DISTRO}" = alpine ] && grep -q '^ID=alpine$' /etc/os-release; then \
      apk add --no-cache python3 git bash ca-certificates; \
    elif [ "${TARGET_DISTRO}" = fedora ] && grep -q '^ID=fedora$' /etc/os-release; then \
      dnf install -y --setopt=install_weak_deps=False \
        python3 git-core ca-certificates nodejs24 nodejs24-npm && \
      ln -s /usr/bin/node-24 /usr/local/bin/node && \
      ln -s /usr/bin/npm-24 /usr/local/bin/npm && \
      dnf clean all; \
    else echo "REFUSE_MISMATCHED_OS" >&2; exit 2; fi; \
    node -e "if (process.versions.node.split('.')[0] !== '24') process.exit(2)" && \
    python3 --version && git --version
COPY manifest/genesis-boot-003.json /usr/share/static-os/genesis-boot-003.json
COPY scripts/stage-genesis-portable.py /usr/local/bin/stage-genesis-portable.py
# Native Git objects are preserved. No merged default-branch assumptions.
RUN python3 /usr/local/bin/stage-genesis-portable.py \
      /usr/share/static-os/genesis-boot-003.json /opt/static-os/genesis-sources && \
    npm ci --prefix /opt/static-os/genesis-sources/garden \
      --ignore-scripts --no-audit --no-fund --loglevel=error && \
    test -f /opt/static-os/genesis-sources/garden/node_modules/tsx/dist/cli.mjs
# Source/worktrees are read-only and their original Git objects retained.
# The genesis user only owns its output folder, never the source histories.
RUN mkdir -p /home/genesis/.local/state/static-genesis/runs && \
    chown -R 10001:10001 /home/genesis && \
    chmod 700 /home/genesis/.local/state/static-genesis/runs
COPY config/multidistro/run-genesis.sh /usr/local/bin/run-genesis
RUN chmod 755 /usr/local/bin/run-genesis && \
    printf 'alpine or fedora OCI candidate; image build is not a booted OS or a physical result\n' \
      > /usr/share/static-os/CLAIM-BOUNDARY.txt
USER 10001:10001
ENV HOME=/home/genesis \
    XDG_STATE_HOME=/home/genesis/.local/state \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_CONFIG_GLOBAL=/usr/share/static-os/genesis-gitconfig \
    NODE_ENV=production
WORKDIR /home/genesis
ENTRYPOINT ["/usr/local/bin/run-genesis"]
