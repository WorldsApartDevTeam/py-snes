        .setcpu "65816"

__startup:
        .org    $0800
        clc
        xce

        rep     #$30    ; 16 bit accumulator and index registers
        .a16
        .i16

main:
        lda     #0
        adc     #5
        sbc     #6

        php
        tsx
        inx
        jsr     debug1

        sta     $7F00
        ldx     #$7F00
        jsr     debug2
        stp

debug1:
        pha             ; push A
        php             ; push flags
        sep     #$20    ; 8-bit A
        .a8
        lda     #1
        sta     $040000
        lda     $0,X
        sta     $040001
        sta     $040004 ; send print command

        plp             ; pull from stack
        pla
        rts

debug2:
        pha             ; push A
        php             ; push flags
        sep     #$20    ; 8-bit A
        .a8
        lda     #2
        sta     $040000
        lda     $0,X
        sta     $040001
        lda     $1,X
        sta     $040002
        sta     $040004 ; send print command

        plp             ; pull from stack
        pla
        rts

debug3:
        pha             ; push A
        php             ; push flags
        sep     #$20    ; 8-bit A
        .a8
        lda     #3
        sta     $040000
        lda     $0,X
        sta     $040001
        lda     $1,X
        sta     $040002
        lda     $2,X
        sta     $040003
        sta     $040004 ; send print command

        plp             ; pull from stack
        pla
        rts
