// PSSM 1.0 Entry 002 D, translated into the SysMLC subset.
package PSSM_Entry002D {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to wait.
        entry; then wait;

        state wait;

        // The UML entry point EntryPoint1 has no outgoing transition;
        // reaching it enters S1 by default entry, which T2 targeting S1
        // expresses directly.
        state S1 {
            // S1's UML entry behavior, followed by the effect of the
            // initial transition T1.1, then the succession to S1.1.
            entry action {
                assign log := log + "S1(entry)::";
                then assign log := log + "T1.1(effect)::";
            } then 'S1.1';

            state 'S1.1';

            transition 'T1.2' first 'S1.1'
                do assign log := log + "T1.2(effect)::" then done;
        }

        transition T2 first wait accept Start
            do assign log := log + "T2(effect)::" then S1;
        transition T3 first S1 then done;
    }
}
