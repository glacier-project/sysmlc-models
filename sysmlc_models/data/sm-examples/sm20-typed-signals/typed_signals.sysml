package SM20 {
    private import ScalarValues::*;

    item def Base {
        attribute value : Integer default 41;
    }
    item def Child :> Base;
    item def Grandchild :> Child;
    item def Left :> Base;
    item def Right :> Base;
    item def Diamond :> Left, Right;
    alias BaseAlias for Base;

    package A {
        item def Alarm;
    }
    package B {
        item def Alarm;
    }

    state def MachineExact {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Base() to commPort then armed;
        transition first armed
            accept signal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
    }

    state def MachineUnrelated {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new B::Alarm() to commPort then armed;
        transition first armed
            accept signal : A::Alarm via commPort
            do action {
                assign count := count + 1;
            }
            then received;
    }

    state def MachineDirectSubtype {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept signal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
    }

    state def MachineTransitiveSubtype {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Grandchild() to commPort then armed;
        transition first armed
            accept signal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
    }

    state def MachineBaseToSubtype {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Base() to commPort then armed;
        transition first armed
            accept signal : Child via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
    }

    state def MachineAlias {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Base() to commPort then armed;
        transition first armed
            accept signal : BaseAlias via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
    }

    state def MachineDiamond {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Diamond() to commPort then armed;
        transition first armed
            accept signal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := signal.value;
            }
            then received;
        // A duplicate delivery must remain observable after the first accept.
        transition first received
            accept Base via commPort
            do assign count := count + 1
            then received;
    }

    state def MachineBaseFirst {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state firstSelected;
        state secondSelected;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept firstSignal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := firstSignal.value;
            }
            then firstSelected;
        transition first armed
            accept secondSignal : Child via commPort
            do action {
                assign count := count + 1;
                then assign captured := secondSignal.value;
            }
            then secondSelected;
    }

    state def MachineSubtypeFirst {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state firstSelected;
        state secondSelected;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept firstSignal : Child via commPort
            do action {
                assign count := count + 1;
                then assign captured := firstSignal.value;
            }
            then firstSelected;
        transition first armed
            accept secondSignal : Base via commPort
            do action {
                assign count := count + 1;
                then assign captured := secondSignal.value;
            }
            then secondSelected;
    }

    state def MachineFalseGuard {
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state firstSelected;
        state secondSelected;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept firstSignal : Base via commPort
            if firstSignal.value > 100
            do action {
                assign count := count + 1;
                then assign captured := firstSignal.value;
            }
            then firstSelected;
        transition first armed
            accept secondSignal : Child via commPort
            do action {
                assign count := count + 1;
                then assign captured := secondSignal.value;
            }
            then secondSelected;
    }

    // The first transition's local binding must not capture the machine
    // attribute in the later transition's effect.
    state def MachineAliasBindings {
        attribute shadow : Integer := 100;
        attribute count : Integer := 0;
        attribute captured : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state rejected;
        state received;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept shadow : Base via commPort
            if shadow.value > 100
            do assign count := count + 1
            then rejected;
        transition first armed
            accept packet : Child via commPort
            do action {
                assign count := count + 1;
                then assign captured := packet.value + shadow;
            }
            then received;
    }
}
