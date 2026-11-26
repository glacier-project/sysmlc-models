// PSSM 1.0 Transition 022, translated into the SysMLC subset.
package PSSM_Transition022 {
    private import ScalarValues::*;

    item def Start;

    state def Machine {
        attribute log : String := "";
        // The UML context attribute `count : Integer`, default 0.
        attribute count : Integer := 0;

        // T1: initial transition to Waiting.
        entry; then Waiting;

        state Waiting;
        state Incrementing;

        transition T2 first Waiting accept Start then Incrementing;
        // The UML guard executes Not(countLowerThan5()); its text reads
        // `this.count == 5`.
        transition T4 first Incrementing if not (count < 5) then done;
        transition T3 first Incrementing if count < 5 do action {
            assign count := count + 1;
            then assign log := log + "T3::";
        } then Incrementing;
    }
}
