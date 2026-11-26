// PSSM 1.0 Transition 001, translated into the SysMLC subset.
package PSSM_Transition001 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to S1.
        entry; then S1;

        state S1;
        state S2;

        transition T2 first S1 accept Start
            do assign log := log + "T2(effect)::" then S2;
        transition T3 first S2 then done;
    }
}
