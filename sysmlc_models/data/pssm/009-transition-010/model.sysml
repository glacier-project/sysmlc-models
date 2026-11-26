package PSSM_Transition010 {
    private import ScalarValues::*;
    item def Start;
    item def AnotherSignal;
    item def Continue;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        state wait { exit action { assign log := log + "Waiting(exit)::"; } }
        state S1 {
            entry action { assign log := log + "S1(entry)::"; } then listening;
            exit action { assign log := log + "S1(exit)::"; }
            state listening;
            transition first listening accept AnotherSignal do assign log := log + "IT::" then listening;
        }
        transition first wait accept Start then S1;
        transition first S1 accept Continue then done;
    }
}
