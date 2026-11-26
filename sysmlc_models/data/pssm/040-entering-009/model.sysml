package PSSM_Entering009 {
    private import ScalarValues::*;
    item def Start;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        state wait;
        state S1 {
            entry action { assign log := log + "S1(entry)::"; then assign log := log + "T1.1(effect)::"; } then 'S1.1';
            state 'S1.1' { entry action { assign log := log + "S1.1(entry)::"; } }
            transition first 'S1.1' then done;
        }
        transition first wait accept Start do assign log := log + "T2(effect)::" then S1;
        transition first S1 then done;
    }
}
