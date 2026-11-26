// PSSM 1.0 Transition 007, translated into the SysMLC subset.
package PSSM_Transition007 {
    private import ScalarValues::*;

    item def Continue;
    item def AnotherSignal;

    state def Machine {
        attribute log : String := "";

        // Initial_S1: initial transition to S1.
        entry; then S1;

        state S1;
        state S2;
        state S3;

        transition T1 first S1 accept AnotherSignal
            do assign log := log + "T1(effect)::" then S3;
        // The UML T2 has two triggers, Continue and AnotherSignal. A SysML
        // transition has one accepter, so T2 is split into one transition
        // per trigger, with the same source, target and effect.
        transition T2 first S3 accept Continue
            do assign log := log + "T2(effect)::" then S1;
        transition T2_AnotherSignal first S3 accept AnotherSignal
            do assign log := log + "T2(effect)::" then S1;
        transition T3 first S1 accept Continue
            do assign log := log + "T3(effect)::" then S2;
        transition T4 first S2 then done;
    }
}
