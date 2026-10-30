package SM21 {
    private import ScalarValues::*;
    item def Named { attribute name : String default "pump-1"; }
    item def Data { attribute data : Integer default 42; }
    item def Delayed { attribute delay : Integer default 5; }
    item def Complete {
        attribute name : String default "pump-1";
        attribute data : Integer default 42;
        attribute delay : Integer default 5;
        attribute payload : Integer default 7;
        attribute _sysmlc_payload : Integer default 11;
    }
    state def MachineName {
        attribute captured : String := "";
        attribute count : Integer := 0;
        port comm;
        entry; then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Named() to comm then armed;
        transition first armed accept packet : Named via comm
            do action {
                assign captured := packet.name;
                then assign count := count + 1;
            } then received;
    }
    state def MachineData {
        attribute captured : Integer := -1;
        attribute count : Integer := 0;
        port comm;
        entry; then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Data() to comm then armed;
        transition first armed accept packet : Data via comm
            do action {
                assign captured := packet.data;
                then assign count := count + 1;
            } then received;
    }
    state def MachineDelay {
        attribute captured : Integer := -1;
        attribute count : Integer := 0;
        port comm;
        entry; then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Delayed() to comm then armed;
        transition first armed accept packet : Delayed via comm
            do action {
                assign captured := packet.delay;
                then assign count := count + 1;
            } then received;
    }
    state def MachineCombined {
        attribute capturedName : String := "";
        attribute total : Integer := 0;
        attribute count : Integer := 0;
        port comm;
        entry; then idle;
        state idle;
        transition first idle do send new Complete() to comm then armed;
        state armed;
        state received;
        transition first armed accept packet : Complete via comm
            do action {
                assign capturedName := packet.name;
                then assign total := packet.data + packet.delay
                    + packet.payload + packet._sysmlc_payload;
                then assign count := count + 1;
            } then received;
    }
    state def MachineExternal {
        attribute capturedName : String := "";
        attribute total : Integer := 0;
        attribute count : Integer := 0;
        port comm;
        entry; then armed;
        state armed;
        state received;
        transition first armed accept packet : Complete via comm
            do action {
                assign capturedName := packet.name;
                then assign total := packet.data + packet.delay
                    + packet.payload + packet._sysmlc_payload;
                then assign count := count + 1;
            } then received;
    }
}
