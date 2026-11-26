// PSSM 1.0 Event 015, translated into the SysMLC subset.
// Transitions are declared in the order of the original XMI.
package PSSM_Event015 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to waiting.
        entry; then waiting;

        state waiting;

        state S1 {
            // T1.1: initial transition to S1.1.
            entry; then 'S1.1';

            state 'S1.1';

            transition 'T1.2' first 'S1.1'
                do assign log := log + "T1.2(effect)::" then done;
            transition 'T1.3' first 'S1.1'
                do assign log := log + "T1.3(effect)::" then done;
        }

        transition T2 first waiting accept Start then S1;
        transition T3 first S1 then done;
    }
}
