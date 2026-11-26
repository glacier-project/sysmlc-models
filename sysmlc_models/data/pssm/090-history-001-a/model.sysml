package PSSM_History001A {
    private import ScalarValues::*;
    item def Start;
    item def AnotherSignal;
    item def Continue;
    state def Machine {
        attribute log : String := "";
        attribute rememberedSecond : Boolean := false;
        entry; then wait;
        state wait;
        state S1 {
            entry action { assign log := log + "S1(entry)::"; } then 'S1.1';
            state 'S1.1' {
                entry action { assign log := log + "S1.1(entry)::"; } then selectLeaf;
                state selectLeaf;
                state 'S1.1.1' { entry action { assign log := log + "S1.1.1(entry)::"; } }
                state 'S1.1.2' {
                    entry action {
                        assign rememberedSecond := true;
                        then assign log := log + "S1.1.2(entry)::";
                    }
                }
                transition first selectLeaf if rememberedSecond then 'S1.1.2';
                transition first selectLeaf if not rememberedSecond then 'S1.1.1';
                transition first 'S1.1.1' then 'S1.1.2';
                transition first 'S1.1.2' accept Continue then done;
            }
            transition first 'S1.1' then done;
        }
        transition first wait accept Start then S1;
        transition first S1 accept AnotherSignal do assign log := log + "T3(effect)::" then S1;
        transition first S1 then done;
    }
}
