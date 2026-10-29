/* Portable schema smoke fixture, compiled on the CI host.
 * This does NOT simulate a Wii/GameCube/DS/ESP32 hardware runtime.
 * It ensures native C firmware and the Python bridge share exact bytes.
 */
#include <stdio.h>
#include <string.h>
#include "../ports/common/genesis_intent.h"
int main(int argc,char **argv){
    if(argc!=3)return 2;
    unsigned idx=0;
    if(strlen(argv[1])!=1||argv[1][0]<'0'||argv[1][0]>'3')return 2;
    idx=(unsigned)(argv[1][0]-'0');
    const char *name=argv[2];
    if(strcmp(name,"NINTENDO_GAMECUBE_SD")!=0 &&
       strcmp(name,"NINTENDO_DS_DLDI")!=0 &&
       strcmp(name,"ESP32_USB_SERIAL")!=0)return 2;
    char out[1024];
    int n=genesis_format_intent(out,sizeof(out),idx,name);
    if(n<=0)return 2;
    return fwrite(out,1,(size_t)n,stdout)==(size_t)n?0:2;
}
