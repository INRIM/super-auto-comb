from pandas import DataFrame

from super_auto_comb.track_changes import df_extract, load_cirt_setup, load_do_setup


def test_load_do_setup():
    df = load_do_setup("LoYb", "./tests/samples")
    assert df.shape == (4, 24)


def test_load_cirt_setup():
    assert load_cirt_setup(60_000, 60_100).shape == (4, 2)


def test_df_extract():
    df = DataFrame([[0, 1], [2, 3]], columns=["1", "2"])
    assert df_extract(df, ["1", "3"]) == ["1"]
