// PSSM 1.0 Event 017 A, translated into the SysMLC subset.
// Transitions are declared in the order of the original XMI.
package PSSM_Event017A {
    private import ScalarValues::*;

    item def Start;
    item def Data {
        attribute value : Boolean;
    }

    state def Machine {
        attribute log : String := "";

        // T1: initial transition to wait.
        entry; then wait;

        state wait;
        state S1;
        state S2;

        transition T2 first wait accept Start then S1;
        transition T3 first S1 accept data : Data if data.value == true
            do assign log := log + "T3(effect)::" then S2;
        // Guard as specified in PSSM 9.3.4.10 and the XMI guard body; the
        // XMI behavior reference of this guard is T3's guard activity.
        transition T4 first S1 accept data : Data if data.value == false
            do assign log := log + "T4(effect)::" then S2;
        transition T5 first S2 then done;
    }
}
