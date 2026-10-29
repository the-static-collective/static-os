/*
 * GENESIS Wii 001 — native Wii PowerPC first-boot porch.
 *
 * No Linux, Node, cloud, WAN, privileged IOS calls, NAND writes, installation,
 * signed receipts or hardware actuation. Wiimote picks one STATIC, public-safe
 * mission question; explicit PLUS/START exports ONE inert file to SD.
 * Only a separately controlled CANNON computer can subsequently execute it.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include <gccore.h>
#include <fat.h>
#include <wiiuse/wpad.h>

#define OUTBOX "sd:/static-genesis"
#define SCHEMA "static-os.wii-first-boot-intent/v1"

static const char *topics[] = {
    "Living House", "Community Food", "Festival Table", "Repair Lab"
};
static const char *questions[] = {
    "Can one Suitcase help an ordinary house become cooperative infrastructure?",
    "Can one Suitcase help a house coordinate a fictional community food table?",
    "Can one Suitcase help a house plan a fictional cooperative festival?",
    "Can one Suitcase help a house plan a fictional repair workshop?"
};
#define TOPICS 4

static char notice[160] = "No SD write, network, or other act yet.";

static int save_request(int selection) {
    if (selection < 0 || selection >= TOPICS) return -1;
    if (!fatInitDefault()) {
        snprintf(notice, sizeof(notice), "SD filesystem unavailable. Nothing saved.");
        return -1;
    }
    if (mkdir(OUTBOX, 0755) < 0 && errno != EEXIST) {
        snprintf(notice, sizeof(notice), "Could not create SD outbox; no change.");
        return -1;
    }
    char path[128];
    for (int n = 1; n <= 999; n++) {
        snprintf(path, sizeof(path), OUTBOX "/intent-%03d.json", n);
        int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0644);
        if (fd < 0) {
            if (errno == EEXIST) continue;
            snprintf(notice, sizeof(notice), "SD storage refused; no existing file overwritten.");
            return -1;
        }
        char body[1024];
        int size = snprintf(body, sizeof(body),
            "{\n"
            "  \"schema\": \"" SCHEMA "\",\n"
            "  \"mission\": \"living-house\",\n"
            "  \"focus\": \"%s\",\n"
            "  \"question\": \"%s\",\n"
            "  \"scenario\": \"FICTIONAL_A_B\",\n"
            "  \"mode\": \"OFFLINE_HOLD_ONLY\",\n"
            "  \"source_device\": \"WII_HOMEBREW_LOCAL_OPERATOR\",\n"
            "  \"operator_action\": \"PLUS_EXPORT_PRESSED\",\n"
            "  \"status\": \"PROPOSAL_ONLY_NOT_EXECUTED\",\n"
            "  \"transmitted\": false,\n"
            "  \"physical_observation\": false,\n"
            "  \"signed\": false,\n"
            "  \"independent_witness\": false\n"
            "}\n", topics[selection], questions[selection]);
        if (size <= 0 || (size_t)size >= sizeof(body)) {
            close(fd); unlink(path);
            snprintf(notice, sizeof(notice), "Request exceeded bounded buffer. Refused.");
            return -1;
        }
        size_t sent = 0;
        while (sent < (size_t)size) {
            ssize_t wrote = write(fd, body + sent, (size_t)size - sent);
            if (wrote <= 0) break;
            sent += (size_t)wrote;
        }
        if (close(fd) < 0 || sent != (size_t)size) {
            unlink(path);
            snprintf(notice, sizeof(notice), "SD write incomplete. No executable request.");
            return -1;
        }
        snprintf(notice, sizeof(notice),
            "Saved intent-%03d.json on SD. Remove SD to carry manually.", n);
        return 0;
    }
    snprintf(notice, sizeof(notice), "Outbox full (999). Nothing overwritten.");
    return -1;
}

static void render(int selected, int confirmed) {
    printf("\x1b[2J\x1b[H");
    printf("  +--------------------------------------------------+\n");
    printf("  |  STATIC COLLECTIVE // GENESIS WII 001            |\n");
    printf("  |            HELLO, WORLD.                          |\n");
    printf("  +--------------------------------------------------+\n\n");
    printf("  What shall we build together?\n\n");
    for (int i = 0; i < TOPICS; ++i) {
        printf("    %c %d. %s\n", selected == i ? '>' : ' ', i + 1, topics[i]);
    }
    printf("\n  A  : preview / approve an inert mission question\n");
    printf("  +/-: PLUS exports to SD only AFTER A approval\n");
    printf("  UP/DOWN: change mission (cancels approval)\n");
    printf("  B  : cancel approval\n");
    printf("  HOME: return to launcher\n\n");
    if (confirmed) {
        printf("  APPROVED FOR FILE EXPORT ONLY:\n");
        printf("  %s\n", questions[selected]);
    } else {
        printf("  HOLD: question not yet approved for SD export.\n");
    }
    printf("\n  %s\n\n", notice);
    printf("  NO INTERNET. NO HOUSE BUILT. NO SIGNED WITNESS.\n");
    printf("  No physical action until separately reviewed.\n");
    fflush(stdout);
}

int main(void) {
    VIDEO_Init();
    WPAD_Init();
    GXRModeObj *rmode = VIDEO_GetPreferredMode(NULL);
    void *xfb = MEM_K0_TO_K1(SYS_AllocateFramebuffer(rmode));
    console_init(xfb, 20, 20, rmode->fbWidth - 40, rmode->xfbHeight - 40,
                 rmode->fbWidth * VI_DISPLAY_PIX_SZ);
    VIDEO_Configure(rmode);
    VIDEO_SetNextFramebuffer(xfb);
    VIDEO_SetBlack(FALSE);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    if (rmode->viTVMode & VI_NON_INTERLACE) VIDEO_WaitVSync();

    int selected = 0, approved = 0;
    render(selected, approved);
    while (SYS_MainLoop()) {
        WPAD_ScanPads();
        u32 key = WPAD_ButtonsDown(0);
        if (key & WPAD_BUTTON_HOME) break;
        if (key & (WPAD_BUTTON_UP | WPAD_BUTTON_DOWN)) {
            selected = (selected + ((key & WPAD_BUTTON_UP) ? TOPICS-1 : 1)) % TOPICS;
            approved = 0;
            snprintf(notice, sizeof(notice), "Mission changed. Approval reset.");
            render(selected, approved);
        } else if (key & WPAD_BUTTON_A) {
            approved = 1;
            snprintf(notice, sizeof(notice), "Question approved for SD export, not execution.");
            render(selected, approved);
        } else if (key & WPAD_BUTTON_B) {
            approved = 0;
            snprintf(notice, sizeof(notice), "Approval cancelled. Nothing transmitted.");
            render(selected, approved);
        } else if (key & WPAD_BUTTON_PLUS) {
            if (!approved) {
                snprintf(notice, sizeof(notice), "REFUSE: press A to approve file first.");
            } else if (save_request(selected) == 0) {
                approved = 0; /* One deliberate gesture per exported intent. */
            }
            render(selected, approved);
        }
        VIDEO_WaitVSync();
    }
    return 0;
}
