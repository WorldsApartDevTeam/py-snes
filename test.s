        .setcpu "65816"

main:
        .org    $0800
        clc
        xce

        .org    $FFFC
__resv:
        .byte $00
        .byte $80
