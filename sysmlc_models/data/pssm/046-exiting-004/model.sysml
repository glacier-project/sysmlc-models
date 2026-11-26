package PSSM_Exiting004 {
    private import ScalarValues::*;
    item def Start;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        state wait;
        state S1 {
            entry; then 'S1.1';
            exit action { assign log := log + "S1(exit)::"; }
            state 'S1.1' { exit action { assign log := log + "S1.1(exit)::"; } }
            transition first 'S1.1' do assign log := log + "T1.2(effect)::" then done;
        }
        transition first wait accept Start then S1;
        transition first S1 then done;
    }
}
