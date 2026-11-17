package SM22 {
    private import ScalarValues::*;
    private import FixedWidthScalarValues::*;

    item def Tick;

    state def Machine {
        attribute count :> uint8 := 250;
        attribute x :> int32 := 2147483647;
        attribute big :> int64 := 0;
        attribute s :> int32 := -1;
        attribute u :> uint32 := 1;
        attribute flag : Boolean := false;
        attribute f :> float32 := 0.5;
        attribute top :> uint64 := 18446744073709551615;
        attribute low :> int64 := -9223372036854775808;
        assert constraint capped { count <= 253 }

        entry; then idle;
        state idle;
        transition first idle accept Tick
            do action {
                assign count := count + 1;
                then assign big := x * x;
                then assign flag := s < u;
                then assign f := f + 0.25;
            }
            then idle;
    }
}
