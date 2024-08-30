from super_auto_comb.calc import beat2y


def test_beat2y():
    assert (
        beat2y(
            f_beat=20e6,
            nominal="194_400_000_000_000",
            N=777_600,
            f_rep=250e6,
            f0=20e6,
            f_beat_sign=-1,
        )
        == 0.0
    )
