package PSSM_Choice001 {
    private import ScalarValues::*;
    item def Start;
    state def Machine {
        attribute log : String := "";
        entry; then wait;
        attribute value : Integer := 0;
        state wait;
        state Increment { entry action { assign value := value + 1; } }
        state Choice1;
        transition first wait accept Start do assign value := 0 then Increment;
        transition first Increment then Choice1;
        transition first Choice1 if value == 5 then done;
        transition first Choice1 if value < 5 do assign log := log + "T4(effect)::" then Increment;
    }
}
