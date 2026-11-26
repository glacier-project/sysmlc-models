// PSSM 1.0 Transition 015, translated into the SysMLC subset.
package PSSM_Transition015 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // Unnamed UML initial transition to waiting.
        entry; then waiting;

        state waiting;

        state S1 {
            entry action { assign log := log + "S1(entry)::"; }
            do action { assign log := log + "S1(doActivity)::"; }
        }

        transition T2 first waiting accept Start then S1;
        transition T3 first S1 then done;
    }
}
