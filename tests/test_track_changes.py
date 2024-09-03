from pandas import DataFrame

from super_auto_comb.track_changes import (
    df_add_name,
    df_extract,
    df_from_cirt,
    load_do_setup,
)


def test_load_do_setup():
    df = load_do_setup("LoYb", "./tests/samples")
    assert df.shape == (5, 26)


def test_df_from_cirt():
    assert df_from_cirt(60_000, 60_100).shape == (4, 2)


def test_df_extract():
    df = DataFrame([[0, 1], [2, 3]], columns=["1", "2"])
    assert df_extract(df, ["1", "3"]) == ["1"]


def test_df_add_name():
    df = DataFrame([["0", "1", "3"], ["0", "2", "3"]], columns=["1", "2", "3"])
    df_add_name(df, fix=["1"], var=["2", "3"])
    assert list(df["name"]) == ["0-1", "0-2"]
