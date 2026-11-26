// PSSM 1.0 Entry 002 A, translated into the SysMLC subset.
package PSSM_Entry002A {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to wait.
        entry; then wait;

        state wait;

        // The two UML regions of S1 become the concurrent substates
        // Region1 and Region2 of the parallel state S1. The UML entry
        // point EntryPoint1 has no outgoing transition; reaching it enters
        // S1 by default entry, which T2 targeting S1 expresses directly.
        state S1 parallel {
            state Region1 {
                // T1.1: initial transition to S1.1.
                entry; then 'S1.1';

                state 'S1.1' {
                    entry action { assign log := log + "S1.1(entry)::"; }
                }

                transition 'T1.2' first 'S1.1' then done;
            }

            state Region2 {
                // T2.1: initial transition to S2.1.
                entry; then 'S2.1';

                state 'S2.1' {
                    entry action { assign log := log + "S2.1(entry)::"; }
                }

                transition 'T2.2' first 'S2.1' then done;
            }
        }

        transition T2 first wait accept Start then S1;
        transition T3 first S1 then done;
    }
}
