# Loaded by Alpine aports scripts/mkimage.sh through the standard mkimg plugin API.
# Real Alpine/musl boot, not a Debian-derived distro or installer.
profile_genesis() {
    profile_standard
    image_name="static-genesis"
    title="STATIC OS GENESIS — Alpine Live"
    desc="An independently controlled, offline-capable founding computer."
    profile_abbrev="genesis"
    arch="x86_64"
    hostname="genesis"
    apkovl="genapkovl-genesis.sh"
    kernel_flavors="lts"
    kernel_cmdline="console=tty0 console=ttyS0,115200"
    syslinux_serial="0 115200"
    syslinux_timeout=30
    apks="$apks nodejs npm python3 git ca-certificates curl bash"
}
