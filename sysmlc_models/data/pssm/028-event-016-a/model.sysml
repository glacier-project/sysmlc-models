package PSSM_Event016A {
    private import ScalarValues::*;
    item def Start;
    item def Continue;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        state wait;
        state S1 {
            entry; then 'S1.1';
            state 'S1.1';
            transition first 'S1.1' accept Continue do assign log := log + "T1.2(effect)::" then done;
        }
        state S2;
        transition first wait accept Start then S1;
        transition first S1 accept Continue do assign log := log + "T3(effect)::" then S2;
        transition first S2 then done;
    }
}
