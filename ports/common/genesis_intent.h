/* Portable GENESIS question contract shared by actual retro + ESP32 code.
 * A fixed public-safe question is a proposed software experiment, never authority.
 * No device location, private identity, physical observation or autonomous act.
 */
#ifndef STATIC_GENESIS_PORTABLE_INTENT_H
#define STATIC_GENESIS_PORTABLE_INTENT_H
#include <stdio.h>
#include <stddef.h>
#define GENESIS_PORTABLE_SCHEMA "static-os.portable-first-boot-intent/v1"
#define GENESIS_NQUESTIONS 4
static const char *const genesis_focus[GENESIS_NQUESTIONS] = {
    "Living House", "Community Food", "Festival Table", "Repair Lab"
};
static const char *const genesis_question[GENESIS_NQUESTIONS] = {
    "Can one Suitcase help an ordinary house become cooperative infrastructure?",
    "Can one Suitcase help a house coordinate a fictional community food table?",
    "Can one Suitcase help a house plan a fictional cooperative festival?",
    "Can one Suitcase help a house plan a fictional repair workshop?"
};
static int genesis_format_intent(char *output, size_t cap, unsigned selected,
                                const char *fixed_device) {
    if (!output || !fixed_device || cap < 128 || selected >= GENESIS_NQUESTIONS)
        return -1;
    int n = snprintf(output, cap,
       "{\n"
       "  \"schema\": \"" GENESIS_PORTABLE_SCHEMA "\",\n"
       "  \"mission\": \"living-house\",\n"
       "  \"focus\": \"%s\",\n"
       "  \"question\": \"%s\",\n"
       "  \"scenario\": \"FICTIONAL_A_B\",\n"
       "  \"mode\": \"OFFLINE_HOLD_ONLY\",\n"
       "  \"source_device\": \"%s\",\n"
       "  \"status\": \"PROPOSAL_ONLY_NOT_EXECUTED\",\n"
       "  \"operator_action\": \"EXPLICIT_LOCAL_EXPORT\",\n"
       "  \"transmitted\": false,\n"
       "  \"physical_observation\": false,\n"
       "  \"signed\": false,\n"
       "  \"independent_witness\": false\n"
       "}\n", genesis_focus[selected], genesis_question[selected], fixed_device);
    return n > 0 && (size_t)n < cap ? n : -1;
}
#endif
