// PSSM 1.0 Event 002, translated into the SysMLC subset.
package PSSM_Event002 {
    private import ScalarValues::*;

    item def Start;
    item def Continue;
    item def AnotherSignal;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to Waiting.
        entry; then Waiting;

        state Waiting;

        state S1 {
            // T1.1: initial transition to S1.1, after S1's entry action.
            entry action { assign log := log + "S1(entry)::"; }
                then 'S1.1';
            exit action { assign log := log + "S1(exit)::"; }

            state 'S1.1' {
                entry action { assign log := log + "S1.1(entry)::"; }
            }
            state 'S2.2';

            transition 'T1.2' first 'S1.1' accept Continue then 'S2.2';
        }

        transition T2 first Waiting accept Start then S1;
        transition T3 first S1 accept AnotherSignal then done;
    }
}
