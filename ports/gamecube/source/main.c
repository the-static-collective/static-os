/* GENESIS GAMECUBE 001 — PowerPC/Flipper front door.
 * GC has no native SD slot. Export ONLY to an operator-owned, supported
 * libfat-accessible SD adapter (SD Gecko / similar); refuses otherwise.
 * This is not a disk/NAND installer, a network client, or CANNON runtime.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <gccore.h>
#include <fat.h>
#include "../../common/genesis_intent.h"

static char status[144]="HOLD: no storage, no file, no field evidence.";
static void draw(unsigned selection,int approved) {
    printf("\x1b[2J\x1b[H");
    puts("  STATIC GENESIS // GAMECUBE PORT");
    puts("  HELLO, WORLD.");
    puts("  What shall we build together?\n");
    for(unsigned i=0;i<GENESIS_NQUESTIONS;i++)
        printf("  %c %s\n",selection==i?'>':' ',genesis_focus[i]);
    printf("\n  D-PAD UP/DOWN: Choose (resets approval)\n");
    printf("  A: Approve one public-safe proposal\n");
    printf("  X: Save approved proposal to FAT SD adapter only\n");
    printf("  B: Cancel approval | START: Exit\n\n");
    printf("  %s\n",approved?"EXPORT APPROVED FOR FILE ONLY.":"HOLD: file export not approved.");
    printf("  %s\n\n",status);
    puts("  No actual house, network, signature or human witness.");
    fflush(stdout);
}
static int export_sd(unsigned selected) {
    if(!fatInitDefault()) {
        snprintf(status,sizeof(status),"REFUSE: no compatible FAT SD adapter.");
        return -1;
    }
    if(mkdir("sd:/static-genesis",0755)<0 && errno!=EEXIST) {
        snprintf(status,sizeof(status),"REFUSE: SD outbox unavailable.");
        return -1;
    }
    char body[1024];
    int n=genesis_format_intent(body,sizeof(body),selected,"NINTENDO_GAMECUBE_SD");
    if(n<0) return -1;
    char name[96];
    for(unsigned i=1;i<=999;i++){
        snprintf(name,sizeof(name),"sd:/static-genesis/intent-%03u.json",i);
        int fd=open(name,O_WRONLY|O_CREAT|O_EXCL,0644);
        if(fd<0){if(errno==EEXIST)continue;break;}
        size_t written=0;
        while(written<(size_t)n) {
            ssize_t count=write(fd,body+written,(size_t)n-written);
            if(count<=0)break;
            written+=(size_t)count;
        }
        int close_result=close(fd);
        if(written!=(size_t)n||close_result<0){
            unlink(name);
            snprintf(status,sizeof(status),"HOLD: SD write incomplete.");
            return -1;
        }
        snprintf(status,sizeof(status),"Saved intent-%03u.json, not executed.",i);
        return 0;
    }
    snprintf(status,sizeof(status),"REFUSE: SD unavailable or all 999 names taken.");
    return -1;
}
int main(void) {
    VIDEO_Init();
    PAD_Init();
    GXRModeObj *mode=VIDEO_GetPreferredMode(NULL);
    void *buffer=MEM_K0_TO_K1(SYS_AllocateFramebuffer(mode));
    console_init(buffer,20,20,mode->fbWidth-40,mode->xfbHeight-40,
                 mode->fbWidth*VI_DISPLAY_PIX_SZ);
    VIDEO_Configure(mode);
    VIDEO_SetNextFramebuffer(buffer);
    VIDEO_SetBlack(FALSE);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    if(mode->viTVMode&VI_NON_INTERLACE) VIDEO_WaitVSync();
    unsigned selected=0;int approved=0;
    draw(selected,approved);
    while(SYS_MainLoop()){
        PAD_ScanPads();
        u32 keys=PAD_ButtonsDown(0);
        if(keys&PAD_BUTTON_START) break;
        if(keys&(PAD_BUTTON_UP|PAD_BUTTON_DOWN)){
            selected=(selected+((keys&PAD_BUTTON_UP)?GENESIS_NQUESTIONS-1:1))%GENESIS_NQUESTIONS;
            approved=0;
            snprintf(status,sizeof(status),"Selection changed. Approval reset.");
            draw(selected,approved);
        }else if(keys&PAD_BUTTON_A){
            approved=1;
            snprintf(status,sizeof(status),"Approved export only. Press X.");
            draw(selected,approved);
        }else if(keys&PAD_BUTTON_B){
            approved=0;
            snprintf(status,sizeof(status),"Cancelled. Nothing sent.");
            draw(selected,approved);
        }else if(keys&PAD_BUTTON_X){
            if(!approved)snprintf(status,sizeof(status),"REFUSE: press A before X.");
            else if(export_sd(selected)==0)approved=0;
            draw(selected,approved);
        }
        VIDEO_WaitVSync();
    }
    return 0;
}
