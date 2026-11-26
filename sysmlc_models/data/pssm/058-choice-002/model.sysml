package PSSM_Choice002 {
    private import ScalarValues::*;
    item def Start;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        state wait;
        state Choice1;
        state S1;
        transition first wait accept Start then Choice1;
        transition T3 first Choice1 if true do assign log := log + "T3(effect)::" then S1;
        transition T4 first Choice1 if true do assign log := log + "T4(effect)::" then S1;
        transition T5 first Choice1 do assign log := log + "T5(effect)::" then S1;
        transition first S1 then done;
    }
}
