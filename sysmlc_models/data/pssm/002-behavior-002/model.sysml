// PSSM 1.0 Behavior 002, translated into the SysMLC subset.
package PSSM_Behavior002 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to S1.
        entry; then S1;

        state S1 {
            exit action { assign log := log + "S1(exit)::"; }
        }

        transition T2 first S1 accept Start then done;
    }
}
