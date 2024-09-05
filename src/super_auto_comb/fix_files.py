import glob
import os
import shutil


def fix_files(dir, date, regex_conflict="%y%m%d_?_Frequ (conflicted).txt"):
    """Find and rename files from K+K counters conflicted by Pcloud cloud sync.

    Parameters
    ----------
    dir : str
        Input directory
    date : datetime date
        Input date
    regex_conflict : str, optional
        Regex matching conflicting files, by default "%y%m%d_?_Frequ (conflicted).txt"

    Returns
    -------
    con_files : list
        List of matching files found and hopefully fixed.
    """
    # Pcloud may have conflicted files
    test = date.strftime(regex_conflict)
    con_files = [os.path.basename(_) for _ in glob.glob(os.path.join(dir, test))]

    for con_name in con_files:
        good_name = con_name.replace(" (conflicted)", "")
        temp_name = "wasconflicted_" + good_name

        # backup of original file if needed
        if os.path.exists(os.path.join(dir, good_name)):
            shutil.copy2(os.path.join(dir, good_name), os.path.join(dir, temp_name))

        # rename conflicted file to normal name (conflicted file has all the data)
        shutil.move(os.path.join(dir, con_name), os.path.join(dir, good_name))

    return con_files


def find_files(dir, date, regex="%y%m%d_?_Frequ.txt"):
    """Return a list of files in a directory, matching the K+K filename format for a given date.

    Parameters
    ----------
    dir : str
        Input directory
    date : datetime date
        Input date
    regex_conflict : str, optional
        Regex for matching files, by default "%y%m%d_?_Frequ.txt"

    Returns
    -------
    files : list
        List of matching files.
    """
    test = date.strftime(regex)
    files = [os.path.basename(_) for _ in glob.glob(os.path.join(dir, test))]
    return files
