/* GENESIS NINTENDO DS / ARM9. Tiny dual-screen console front door.
 * DLDI-compatible FAT/SD media required for export, not present on all DS
 * systems. No Wi-Fi/automatic upload, flashcart installation or full CANNON.
 */
#include <nds.h>
#include <fat.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include "../../common/genesis_intent.h"

static unsigned selected=0;
static int approved=0;
static char status[96]="Offline. No file or physical act.";
static void show(void){
    consoleClear();
    iprintf("STATIC GENESIS / NINTENDO DS\n");
    iprintf("HELLO, WORLD.\n");
    iprintf("What shall we build?\n\n");
    for(unsigned i=0;i<GENESIS_NQUESTIONS;i++)
        iprintf("%c %s\n",selected==i?'>':' ',genesis_focus[i]);
    iprintf("\nD-PAD: choose\nA: approve SD export\nX: export (only after A)\n");
    iprintf("B: cancel | START: exit\n");
    iprintf("\n%s\n",approved?"EXPORT APPROVED ONLY":"HOLD: not approved");
    iprintf("%s\n",status);
    iprintf("No Wi-Fi, house, or witness.\n");
}
static int export_intent(void){
    if(!fatInitDefault()){
        snprintf(status,sizeof(status),"No compatible DLDI FAT media.");
        return -1;
    }
    if(mkdir("fat:/static-genesis",0755)<0 && errno!=EEXIST){
        snprintf(status,sizeof(status),"Cannot create FAT outbox.");
        return -1;
    }
    char data[1024];
    int length=genesis_format_intent(data,sizeof(data),selected,"NINTENDO_DS_DLDI");
    if(length<=0)return -1;
    for(unsigned i=1;i<=999;i++){
        char filename[96];
        snprintf(filename,sizeof(filename),"fat:/static-genesis/intent-%03u.json",i);
        int fd=open(filename,O_WRONLY|O_CREAT|O_EXCL,0644);
        if(fd<0){if(errno==EEXIST)continue;break;}
        size_t done=0;
        while(done<(size_t)length){
            ssize_t count=write(fd,data+done,(size_t)length-done);
            if(count<=0)break;
            done+=(size_t)count;
        }
        int closed=close(fd);
        if(done!=(size_t)length||closed<0){
            unlink(filename);
            snprintf(status,sizeof(status),"Incomplete write refused.");
            return -1;
        }
        snprintf(status,sizeof(status),"Saved intent-%03u (no execution).",i);
        return 0;
    }
    snprintf(status,sizeof(status),"Outbox full or FAT unavailable.");
    return -1;
}
int main(void){
    consoleDemoInit();
    show();
    while(1){
        scanKeys();
        int keys=keysDown();
        if(keys&KEY_START)break;
        if(keys&(KEY_UP|KEY_DOWN)){
            selected=(selected+((keys&KEY_UP)?GENESIS_NQUESTIONS-1:1))%GENESIS_NQUESTIONS;
            approved=0;
            snprintf(status,sizeof(status),"Selection changed, reset approval.");
            show();
        }else if(keys&KEY_A){
            approved=1;
            snprintf(status,sizeof(status),"Approved export only; X saves.");
            show();
        }else if(keys&KEY_B){
            approved=0;
            snprintf(status,sizeof(status),"Approval cancelled.");
            show();
        }else if(keys&KEY_X){
            if(!approved)snprintf(status,sizeof(status),"REFUSE: press A before X.");
            else if(export_intent()==0)approved=0;
            show();
        }
        swiWaitForVBlank();
    }
    return 0;
}
