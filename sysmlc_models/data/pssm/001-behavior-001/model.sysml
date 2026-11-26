// PSSM 1.0 Behavior 001, translated into the SysMLC subset.
package PSSM_Behavior001 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to S1.
        entry; then S1;

        state S1 {
            entry action { assign log := log + "S1(entry)::"; }
        }

        transition T2 first S1 accept Start then done;
    }
}
