// PSSM 1.0 Entering 011, translated into the SysMLC subset.
package PSSM_Entering011 {
    private import ScalarValues::*;

    item def Start;
    item def Continue;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to waiting.
        entry; then waiting;

        state waiting;

        // The two UML regions of S1 become the concurrent substates
        // Region1 and Region2 of the parallel state S1. Each region's
        // initial transition effect is its entry action, followed by the
        // succession to the region's initial substate.
        state S1 parallel {
            entry action { assign log := log + "S1(entry)::"; }

            state Region1 {
                // T2.1: initial transition to S1.2, with its effect.
                entry action { assign log := log + "T2.1(effect)::"; }
                    then 'S1.2';

                state 'S1.2' {
                    entry action { assign log := log + "S1.2(entry)::"; }
                }

                transition 'T2.2' first 'S1.2' then done;
            }

            state Region2 {
                // T1.1: initial transition to S1.1, with its effect.
                entry action { assign log := log + "T1.1(effect)::"; }
                    then 'S1.1';

                state 'S1.1' {
                    entry action { assign log := log + "S1.1(entry)::"; }
                }

                transition 'T1.2' first 'S1.1' then done;
            }
        }

        transition T2 first waiting accept Start then S1;
        transition T3 first S1 accept Continue then done;
    }
}
