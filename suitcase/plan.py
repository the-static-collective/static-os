"""STATIC OS Suitcase Genesis 001: read-only, deterministic mission composer.

This module never installs packages, touches disks, generates keys, opens a socket,
or authorizes a federated crossing. A plan is NOT an installed or safe system.
"""
import hashlib
import json
import platform
import shutil
from pathlib import Path

SCHEMA = 'static-os.suitcase-plan/v0'
INVENTORY_SCHEMA = 'static-os.hardware-observation/v0'
PROFILES = {
    'commons': ('tablelight', 'organization-foundry', 'relatte-receiver'),
    'church': ('tablelight', 'offline-library', 'relatte-receiver'),
    'resilience': ('offline-library', 'local-relay', 'relatte-receiver'),
    'protected': ('private-room', 'offline-library', 'relatte-receiver'),
    'foundry': ('organization-foundry', 'tablelight', 'replication-kit'),
}
MEDIA = ('seed', 'grow', 'forest')
PRIVACY = ('private', 'invitation-only', 'public-candidate')
LINKS = ('ethernet', 'wifi', 'bluetooth', 'usb-storage', 'radio-unverified')


def exact_fields(data, fields, label):
    if not isinstance(data, dict) or set(data) != set(fields):
        raise ValueError(f'{label}: unknown or missing fields')


def positive_int(value, label):
    if type(value) is not int or not 0 <= value <= 1000000000:
        raise ValueError(f'{label}: invalid nonnegative integer')


def validate_inventory(inv):
    exact_fields(inv, ('schema', 'architecture', 'ram_mib', 'workspace_free_mib',
                       'links_observed', 'power_observation'), 'inventory')
    if inv['schema'] != INVENTORY_SCHEMA:
        raise ValueError('unsupported inventory schema')
    if inv['architecture'] not in ('amd64', 'arm64', 'unsupported'):
        raise ValueError('unknown architecture')
    positive_int(inv['ram_mib'], 'ram_mib')
    positive_int(inv['workspace_free_mib'], 'workspace_free_mib')
    if (not isinstance(inv['links_observed'], list)
            or len(inv['links_observed']) != len(set(map(str, inv['links_observed'])))
            or any(x not in LINKS for x in inv['links_observed'])):
        raise ValueError('invalid link observations')
    if inv['power_observation'] not in ('unknown', 'ac-present', 'battery-present'):
        raise ValueError('invalid power observation')
    return inv


def probe():
    """Read-only host survey, NOT a destination disk or working network survey."""
    machine = platform.machine().lower()
    arch = {'x86_64': 'amd64', 'amd64': 'amd64',
            'aarch64': 'arm64', 'arm64': 'arm64'}.get(machine, 'unsupported')
    ram = 0
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                ram = int(line.split()[1]) // 1024
                break
    except (OSError, ValueError, IndexError):
        pass
    links = []
    try:
        for nic in Path('/sys/class/net').iterdir():
            if nic.name == 'lo':
                continue
            if (nic / 'wireless').exists():
                links.append('wifi')
            elif (nic / 'type').read_text().strip() == '1':
                links.append('ethernet')
    except OSError:
        pass
    try:
        usage = shutil.disk_usage(Path.cwd())
        workspace_free = usage.free // (1024 * 1024)
    except OSError:
        workspace_free = 0
    return validate_inventory({
        'schema': INVENTORY_SCHEMA, 'architecture': arch, 'ram_mib': ram,
        'workspace_free_mib': workspace_free,
        'links_observed': sorted(set(links)), 'power_observation': 'unknown',
    })


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def compose(inventory, profile, media='seed', privacy='private'):
    validate_inventory(inventory)
    if profile not in PROFILES or media not in MEDIA or privacy not in PRIVACY:
        raise ValueError('unknown profile/media/privacy')
    if profile == 'protected' and privacy == 'public-candidate':
        raise ValueError('protected profile cannot request public discovery')
    holds = []
    if inventory['architecture'] != 'amd64':
        holds.append('NO_VERIFIED_BASE_IMAGE_FOR_ARCH')
    if inventory['ram_mib'] < 2048:
        holds.append('INSUFFICIENT_OBSERVED_RAM_FOR_CANDIDATE')
    if inventory['workspace_free_mib'] < 8192:
        holds.append('INSUFFICIENT_BUILD_WORKSPACE_FREE_SPACE')
    # Neither source packages nor offline caches are available in this specimen.
    holds.append('OS_AND_APPLICATION_PAYLOADS_NOT_SUPPLIED')
    if media in ('grow', 'forest'):
        holds.append('OFFLINE_PACKAGE_CLOSURE_NOT_VERIFIED')
    plan = {
        'schema': SCHEMA,
        'kind': 'PROPOSAL_ONLY',
        'status': 'HOLD_FOR_BUILD_AND_HUMAN_REVIEW',
        'request': {'profile': profile, 'media': media, 'privacy': privacy},
        'hardware_observation': json.loads(canonical(inventory)),
        'foundation_candidate': {'family': 'debian', 'codename': 'bookworm',
                                 'architecture': 'amd64', 'existing_image': 'unverified'},
        'capabilities': [{'name': name, 'state': 'NOT_PACKAGED',
                          'activation': 'EXPLICIT_LOCAL_OPT_IN'} for name in PROFILES[profile]],
        'federation': {'discovery': 'DISABLED', 'outbound': 'DISABLED',
                       'acceptance': 'RECEIVER_LOCAL_ONLY',
                       'ancestry': 'PRIVATE_UNTIL_CONSENTED'},
        'hardware_effects': {'disk_write': False, 'network_send': False,
                             'radio_transmit': False, 'service_start': False},
        'identity': {'organization': 'NOT_FOUNDED', 'keys': 'NOT_GENERATED',
                     'user_consent': 'NOT_ESTABLISHED'},
        'holds': holds,
        'claim_limits': [
            'NO_OS_INSTALL', 'NO_BOOT_PROOF', 'NO_PERSISTENCE_PROOF',
            'NO_HUMAN_IDENTITY_VERIFICATION', 'NO_REAL_PARTNER_OR_RESOURCE',
            'NO_TRANSPORT_OR_CRYPTOGRAPHIC_CROSSING',
        ],
    }
    plan['plan_sha256'] = hashlib.sha256(canonical(plan).encode('ascii')).hexdigest()
    return plan


def verify(plan):
    if not isinstance(plan, dict) or 'request' not in plan or 'hardware_observation' not in plan:
        raise ValueError('not a suitcase plan')
    req = plan['request']
    exact_fields(req, ('profile', 'media', 'privacy'), 'request')
    expected = compose(plan['hardware_observation'], req['profile'], req['media'], req['privacy'])
    if plan != expected:
        raise ValueError('plan modified, escalated or inconsistent')
    return True
