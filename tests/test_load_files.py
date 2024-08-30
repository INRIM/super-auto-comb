from datetime import datetime

from super_auto_comb.load_files import genfromkk


def test_genfromkk():
    assert genfromkk("./tests/samples/220321_1_Frequ.txt").shape == (3600, 13)
