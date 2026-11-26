// PSSM 1.0 Exiting 001, translated into the SysMLC subset.
package PSSM_Exiting001 {
    private import ScalarValues::*;

    item def Start;
    item def Continue;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to waiting.
        entry; then waiting;

        state waiting;

        // The two UML regions of S1 become the concurrent substates
        // Region1 and Region2 of the parallel state S1.
        state S1 parallel {
            exit action { assign log := log + "S1(exit)::"; }

            state Region1 {
                // T1.1: initial transition to S1.1.
                entry; then 'S1.1';

                state 'S1.1' {
                    // T1.1.1: initial transition to S1.1.1.
                    entry; then 'S1.1.1';
                    exit action { assign log := log + "S1.1(exit)::"; }

                    state 'S1.1.1' {
                        exit action { assign log := log + "S1.1.1(exit)::"; }
                    }
                }
            }

            state Region2 {
                // Unnamed UML initial transition to S2.1.
                entry; then 'S2.1';

                state 'S2.1' {
                    exit action { assign log := log + "S2.1(exit)::"; }
                }
            }
        }

        transition T2 first waiting accept Start then S1;
        transition T3 first S1 accept Continue then done;
    }
}
