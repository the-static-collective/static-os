"""HOUSE-SEED-001: read-only house-generation plan composed by the Suitcase.

The house is a *target* for the portable OS, never an automatic installation.
This module intentionally has no I/O, networking, subprocess, identity or actuation.
"""
import hashlib
import json

from suitcase.plan import compose, verify, canonical, exact_fields

SURVEY_SCHEMA = 'static-os.house-site-survey/v0'
HOUSE_SCHEMA = 'static-os.living-house-seed/v0'
OBSERVATIONS = ('UNOBSERVED', 'PRESENT_UNVERIFIED', 'ABSENT')
SLOTS = ('utility', 'roof_or_window', 'entry_floor', 'wall_hall',
         'kitchen_garden', 'living_room', 'independent_peer')
PARTS = ('computer', 'approved_usb_power', 'solar_module', 'solar_controller',
         'pressure_sensor', 'optical_tx_rx', 'environment_sensor', 'peer_device')
NO_EFFECTS = {'disk_write': False, 'network_send': False,
              'radio_transmit': False, 'service_start': False,
              'physical_actuation': False, 'building_modification': False}

# Spaces are *opportunities*, not permission to modify a building. Every gate
# yields an evidence request for a human, never a hardware-driving command.
MODULES = (
    ('local_brain', 'utility', ('computer', 'approved_usb_power'),
     'Independent portable core and offline/public-safe workbench',
     'Offline reload on separately controlled test device; record time and errors'),
    ('solar_budget', 'roof_or_window', ('solar_module', 'solar_controller'),
     'Supervised low-voltage solar input, not a house power supply',
     'Record measured voltage, current, Wh and time against a reference meter'),
    ('floor_sense', 'entry_floor', ('pressure_sensor',),
     'Benchtop step/pressure sensor; energy harvesting is optional research',
     'Count true/false triggers; measure harvested joules only if instrumented'),
    ('light_link', 'wall_hall', ('optical_tx_rx',),
     'Short-range LED/photodiode information link in a safe enclosure',
     'Record payload length, distance, received bits and bit-error count'),
    ('food_and_environment', 'kitchen_garden', ('environment_sensor',),
     'Environment observations and human-reviewed surplus-resource proposal',
     'Record calibration uncertainty and one fictional HOLD-only resource offer'),
    ('human_voice', 'living_room', ('computer',),
     'Voice OR typed intent to a review queue; microphone disabled by default',
     'Demonstrate a text request and explicit approval before any proposed action'),
    ('independent_federation', 'independent_peer', ('peer_device',),
     'Separate keys, signed file crossing and receiver-local refusal',
     'Independent operator signs HOLD/REFUSE; retain matching digests'),
    ('relational_bay', 'wall_hall', ('optical_tx_rx',),
     'Optional tranchNOSE fixture: variable physical configuration, no theory promoted',
     'Run A/B/A physical geometry trial; compare measured states against controls'),
)

STAGES = (
    {'id': '01', 'name': 'SUITCASE_TO_UTILITY_ROOM',
     'work': 'Bench the portable computer on intact certified low-voltage power; do not install or rewire.',
     'evidence': 'Read-only inventory, approved-power inspection, offline restart observation'},
    {'id': '02', 'name': 'HOUSE_SURFACES_AS_INSTRUMENTS',
     'work': 'Try independent solar metering, pressure sensing and optical signaling in removable rigs.',
     'evidence': 'Raw energy readings, sensor baselines, optical bit-error counts and failed trials'},
    {'id': '03', 'name': 'HUMAN_SPEECH_TO_PROPOSAL',
     'work': 'Translate speech OR typed request into an inspectable proposal with explicit human review.',
     'evidence': 'Prompt, proposal, approval/refusal state; no automatic building control'},
    {'id': '04', 'name': 'SECOND_INDEPENDENT_NODE',
     'work': 'Exchange public-safe signed files with a second consenting holder; preserve local refusal.',
     'evidence': 'Two distinct public keys, signed offer/refusal and independently kept receipts'},
    {'id': '05', 'name': 'REPRODUCE_NOT_SUBORDINATE',
     'work': 'Give another steward the kit and instructions; they choose their own governance and may refuse.',
     'evidence': 'Separate self-reported field record; no inherited organizational authority'},
)

def empty_survey():
    """A blank house model, intentionally asserting zero verified resources."""
    return {'schema': SURVEY_SCHEMA, 'building_type': 'SINGLE_HOUSE_MODEL',
            'spaces': {k: 'UNOBSERVED' for k in SLOTS},
            'parts': {k: 'UNOBSERVED' for k in PARTS},
            'site_permission': 'NOT_VERIFIED',
            'information_scope': 'PUBLIC_SAFE_ONLY'}

def validate_survey(survey):
    exact_fields(survey, ('schema', 'building_type', 'spaces', 'parts',
                          'site_permission', 'information_scope'), 'site survey')
    if survey['schema'] != SURVEY_SCHEMA or survey['building_type'] != 'SINGLE_HOUSE_MODEL':
        raise ValueError('unsupported house model')
    if survey['site_permission'] not in ('NOT_VERIFIED', 'OPERATOR_SELF_ATTESTED'):
        raise ValueError('invalid site-permission observation')
    if survey['information_scope'] != 'PUBLIC_SAFE_ONLY':
        raise ValueError('confidential or personal site data refused')
    exact_fields(survey['spaces'], SLOTS, 'house space map')
    exact_fields(survey['parts'], PARTS, 'house parts map')
    if any(type(v) is not str or v not in OBSERVATIONS for v in
           list(survey['spaces'].values()) + list(survey['parts'].values())):
        raise ValueError('unrecognized or malformed house observation')
    return survey

def compose_house(inventory, survey, profile='foundry', media='grow', privacy='private'):
    """Deterministic physical *construction plan* from operator observations.

    Even an all-PRESENT_UNVERIFIED survey never creates an installed state or
    authorizes wiring, surveillance, transmission, network outreach or actuation.
    """
    validate_survey(survey)
    base = compose(inventory, profile, media, privacy)
    modules = []
    for module_id, slot, required, purpose, evidence in MODULES:
        missing = [p for p in required if survey['parts'][p] != 'PRESENT_UNVERIFIED']
        if survey['spaces'][slot] != 'PRESENT_UNVERIFIED':
            missing.append('SPACE_' + slot.upper() + '_NOT_INSPECTED')
        modules.append({
            'id': module_id, 'placement_candidate': slot,
            'purpose': purpose, 'required_parts': list(required),
            'part_observations': {p: survey['parts'][p] for p in required},
            'state': 'BENCH_CANDIDATE_UNVERIFIED' if not missing else 'HOLD_FOR_SITE_SURVEY',
            'holds': missing,
            'test_receipt_to_collect': evidence,
            'authority': 'HUMAN_REVIEW_REQUIRED',
            'automatic_actuation': False,
        })
    plan = {
        'schema': HOUSE_SCHEMA, 'kind': 'REPRODUCIBLE_CONSTRUCTION_PROPOSAL',
        'status': 'HOLD_FOR_SITE_POWER_SAFETY_AND_HUMAN_REVIEW',
        'mission': 'BUILD_ONE_HOUSE_AS_A_MODEL_OF_A_COOPERATIVE_CITY',
        'parent_suitcase_plan': base,
        'site_survey': json.loads(canonical(survey)),
        'modules': modules,
        'stages': json.loads(canonical(STAGES)),
        'hardware_effects': dict(NO_EFFECTS),
        'network': {'default': 'OFFLINE_PRIVATE',
                    'discovery': 'DISABLED',
                    'physical_io': 'BENCH_ONLY_AFTER_INDEPENDENT_AUTHORIZATION',
                    'consent': 'NOT_ESTABLISHED_BY_SITE_SURVEY'},
        'outputs': {
            'construction_recipe': 'THIS_INSPECTABLE_PLAN',
            'human_work_cards': 'STAGES_AND_TEST_RECEIPTS',
            'public_safe_site_map': 'PLACEMENT_CANDIDATES_NOT_CONSTRUCTION_PERMITS',
            'os_image': 'NOT_BUILT',
            'real_home': 'NOT_BUILT',
            'federation': 'NOT_ESTABLISHED',
            'jurisdiction_or_stewardship': 'NOT_ESTABLISHED',
        },
        'research_tracks': {
            'cooperative_computing': 'SIGNED_REFUSAL_AND_RECEIPT_TEST',
            'energy_aware_surfaces': 'MEASURE_POWER_NO_FREE_ENERGY_CLAIM',
            'relational_physical_state': 'TRANCHNOSE_ABA_EXPERIMENT_NO_PROOF_CLAIM',
        },
        'source_owners': {
            'os_composer': 'the-static-collective/static-os',
            'signed_browser_specimen': 'the-static-collective/webZ:bridge/suitcase',
            'crossing_research': 'the-static-collective/reLATTE',
            'physical_field_experiment': 'the-static-collective/tranchNOSE',
            'hardware_research': 'the-static-collective/GHoT',
            'intent_router': 'the-static-collective/JAR-VIS',
        },
        'claims_not_earned': [
            'NO_BOOTABLE_OS_OR_INSTALLER',
            'NO_VERIFIED_POWER_YIELD_OR_SAFE_BUILDING_WIRING',
            'NO_PUBLIC_INFRASTRUCTURE_PERMISSION',
            'NO_OPTICAL_LINK_DEMONSTRATED',
            'NO_RELATIONAL_MEMORY_PROOF',
            'NO_AUTONOMOUS_SPEECH_ACTUATION',
            'NO_RELATTE_WIRE_COMPATIBILITY',
            'NO_REAL_ORGANIZATION_OR_INDEPENDENT_STEWARD_VERIFIED',
        ],
    }
    plan['plan_sha256'] = hashlib.sha256(canonical(plan).encode('ascii')).hexdigest()
    return plan

def verify_house(plan):
    """Cold reconstruction: refuse omissions, altered authority or forged outcomes."""
    if not isinstance(plan, dict) or 'parent_suitcase_plan' not in plan or 'site_survey' not in plan:
        raise ValueError('not a living-house construction plan')
    base = plan['parent_suitcase_plan']
    if not verify(base):
        raise ValueError('unverified parent')
    req = base['request']
    expected = compose_house(base['hardware_observation'], plan['site_survey'],
                             req['profile'], req['media'], req['privacy'])
    if plan != expected:
        raise ValueError('living-house plan modified or authority escalated')
    return True
