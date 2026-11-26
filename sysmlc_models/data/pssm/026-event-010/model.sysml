// PSSM 1.0 Event 010, translated into the SysMLC subset.
// Transitions are declared in the order of the original XMI.
package PSSM_Event010 {
    private import ScalarValues::*;

    item def Start;
    item def Continue;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to waiting.
        entry; then waiting;

        state waiting;

        state S1 {
            // T1.1: initial transition to S1.1, after S1's entry action.
            entry action { assign log := log + "S1(entry)::"; }
                then 'S1.1';

            state 'S1.1' {
                entry action { assign log := log + "S1.1(entry)::"; }
            }
            state 'S1.2' {
                entry action { assign log := log + "S1.2(entry)::"; }
            }
            state 'S1.3' {
                entry action { assign log := log + "S1.3(entry)::"; }
            }

            transition 'T1.2' first 'S1.1' accept Continue
                do assign log := log + "T1.2(effect)::" then 'S1.2';
            transition 'T1.3' first 'S1.1' accept Continue
                do assign log := log + "T1.3(effect)::" then 'S1.3';
            transition 'T1.4' first 'S1.2' then done;
            transition 'T1.5' first 'S1.3' then done;
        }

        state S2 {
            entry action { assign log := log + "S2(entry)::"; }
        }

        transition T2 first waiting accept Start
            do assign log := log + "T2(effect)::" then S1;
        transition T3 first waiting accept Start
            do assign log := log + "T3(effect)::" then S2;
        transition T5 first S2 then done;
        transition T4 first S1 then done;
    }
}
