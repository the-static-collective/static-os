/*
 * GENESIS ESP32 001 — USB-serial / UART0 human proposal terminal.
 * NO Wi-Fi initialization, Bluetooth, GPIO actuation, sensor claims, NVS or
 * automatic outbound packet. Serial output is consciously captured by a human,
 * not an authenticated signed hardware receipt. Firmware installation is a
 * separately controlled operator activity, not performed by this application.
 */
#include <stdio.h>
#include <string.h>
#include "driver/uart.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "../../common/genesis_intent.h"
#define PORT UART_NUM_0
static unsigned selected=0;
static int approved=0;
static void draw(void){
    printf("\nSTATIC GENESIS // ESP32 USB SERIAL\n");
    printf("HELLO, WORLD. What shall we build together?\n");
    for(unsigned i=0;i<GENESIS_NQUESTIONS;i++)
        printf("%c %u. %s\n",selected==i?'>':' ',i+1,genesis_focus[i]);
    puts("1-4: choose | A: approve export | X: emit JSON | C: cancel");
    printf("%s\n",approved?"APPROVED FOR SERIAL EXPORT ONLY":"HOLD: export not approved");
    puts("NO RADIO. NO ACTUATION. NO SIGNATURE OR WITNESS.");
    fflush(stdout);
}
void app_main(void){
    if(uart_driver_install(PORT,1024,0,0,NULL,0)!=ESP_OK){
        puts("REFUSE: UART driver unavailable");return;
    }
    draw();
    while(1){
        unsigned char byte=0;
        int n=uart_read_bytes(PORT,&byte,1,pdMS_TO_TICKS(200));
        if(n!=1)continue;
        if(byte>='1'&&byte<='4'){
            selected=(unsigned)(byte-'1');approved=0;
            draw();
        }else if(byte=='a'||byte=='A'){
            approved=1;puts("Approved one local JSON emission only.");
        }else if(byte=='c'||byte=='C'){
            approved=0;puts("Cancelled. Nothing emitted.");
        }else if(byte=='x'||byte=='X'){
            if(!approved){puts("HOLD: press A before X.");continue;}
            char body[1024];
            int len=genesis_format_intent(body,sizeof(body),selected,"ESP32_USB_SERIAL");
            if(len<=0){puts("HOLD: oversized intent refused.");continue;}
            approved=0;
            puts("BEGIN_STATIC_GENESIS_JSON");
            fwrite(body,1,(size_t)len,stdout);
            puts("END_STATIC_GENESIS_JSON");
            fflush(stdout);
            puts("Copy ONLY the JSON body to the offline importer. No network transmission.");
        }
    }
}
