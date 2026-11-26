// PSSM 1.0 Event 001, translated into the SysMLC subset.
package PSSM_Event001 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to wait.
        entry; then wait;

        state wait {
            exit action { assign log := log + "wait(exit)::"; }
        }

        transition T2 first wait accept Start then done;
    }
}
