import shutil

import tintervals.rocitlinks as rl

from super_auto_comb.cli import main, parse_args


def test_parse_args():
    parser = parse_args("--do LoYb --start -1 --track-cirt".split(" "))
    assert parser.do == ["LoYb"]
    assert parser.start == "-1"
    assert parser.track_cirt is True


def test_parse_args_from_config():
    parser = parse_args("-c ./tests/samples/super-auto-comb.txt".split(" "))
    assert parser.do == ["LoYb"]
    assert parser.start == "59658"
    assert parser.track_cirt is True


def test_main():
    # delete previous results
    try:
        shutil.rmtree("./tests/Outputs/")
    except FileNotFoundError:
        pass
    args = parse_args(
        "--do LoYb --start 59658 --stop 59660 --dir ./tests/Outputs --fig-dir ./tests/Outputs/Figures --comb-dir ./tests/samples --setup-dir ./tests/samples --track-cirt".split(
            " "
        )
    )
    main(args)
    rocit_data = rl.load_link_from_dir("./tests/Outputs/2022-03/INRIM_HM-INRIM_LoYb")
    assert len(rocit_data.t) == 3600
    assert rocit_data.oscA.name == "INRIM_LoYb"


def test_main_from_config():
    # delete previous results
    try:
        shutil.rmtree("./tests/Outputs/")
    except FileNotFoundError:
        pass
    args = parse_args("-c ./tests/samples/super-auto-comb.txt".split(" "))
    main(args)
    rocit_data = rl.load_link_from_dir("./tests/Outputs/2022-03/INRIM_HM-INRIM_LoYb")
    assert len(rocit_data.t) == 3600
    assert rocit_data.oscA.name == "INRIM_LoYb"
