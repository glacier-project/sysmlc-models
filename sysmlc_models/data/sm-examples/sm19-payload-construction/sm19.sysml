package SM19 {
    private import ScalarValues::*;

    item def Marker;
    item def Data {
        attribute x : Integer default 7;
        attribute y : Integer default 9;
    }
    item def Child :> Data;
    item def Redefined :> Data {
        attribute :>> x default 11;
    }

    // Positional arguments bind the public fields in declaration order.
    state def MachinePositional {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Data(13, 42) to commPort then armed;
        transition first armed
            accept r : Data via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // A named argument binds its own field; the omitted field keeps its
    // default.
    state def MachineNamedPartial {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Data(y = 42) to commPort then armed;
        transition first armed
            accept r : Data via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // Without arguments every field takes its default.
    state def MachineDefaults {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Data() to commPort then armed;
        transition first armed
            accept r : Data via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // A specialization carries the inherited fields and their defaults.
    state def MachineInheritedDefaults {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Child() to commPort then armed;
        transition first armed
            accept r : Child via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // A named argument can bind an inherited field.
    state def MachineInheritedNamed {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Child(x = 42) to commPort then armed;
        transition first armed
            accept r : Child via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // A redefinition's own default replaces the inherited default.
    state def MachineRedefinedDefault {
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Redefined() to commPort then armed;
        transition first armed
            accept r : Redefined via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // An argument expression is evaluated when the send is performed. The
    // sender changes current before and after the send; the receiver must
    // observe neither the initial value nor the later one.
    state def MachineSendTimeArgument {
        attribute current : Integer := 1;
        attribute capturedX : Integer := -1;
        attribute capturedY : Integer := -1;
        port commPort;
        entry;
            then idle;
        state idle {
            entry assign current := 40;
        }
        state armed {
            entry assign current := 100;
        }
        state received;
        transition first idle
            do send new Data(y = current + 2) to commPort
            then armed;
        transition first armed
            accept r : Data via commPort
            do action {
                assign capturedX := r.x;
                then assign capturedY := r.y;
            }
            then received;
    }

    // A marker type has no data fields and is delivered as a plain signal.
    state def MachineMarker {
        port commPort;
        entry;
            then idle;
        state idle;
        state armed;
        state received;
        transition first idle do send new Marker() to commPort then armed;
        transition first armed accept Marker via commPort then received;
    }
}
