// PSSM 1.0 Transition 016, translated into the SysMLC subset.
package PSSM_Transition016 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to waiting.
        entry; then waiting;

        state waiting;
        state S1;

        transition T2 first waiting accept Start
            do assign log := log + "T2(effect)::" then S1;
        transition T3 first S1 then done;
    }
}
