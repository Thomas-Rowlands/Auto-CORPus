import datetime
import os
import re
import logging

logging.basicConfig(filename=F"ComparisonLog_{str(datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S'))}.log",
                    filemode="w", level=logging.DEBUG)


def scan_files(folder1_path, folder2_path, journal="pmc", lines_to_ignore=None, file_type="_bioc"):
    """
    Compare text files between two folders and identify files with differences.

    Args:

        folder1_path (str): Path to the first folder containing text files.
        folder2_path (str): Path to the second folder containing text files for comparison.
        journal (str, optional): Journal identifier. Defaults to "pmc".
        lines_to_ignore (list, optional): List of strings indicating lines to ignore during comparison. Defaults to None.
        file_type (str): '_bioc', '_tables' or '_abbreviations' indicating which file to scan.

    Returns:
        list: List of filenames with differences between the corresponding files in the two folders.
    """
    # Initialize lines_to_ignore if not provided
    if not lines_to_ignore:
        lines_to_ignore = []

    # List to store filenames with differences
    different_files = []

    # Walk through folder1_path and compare files
    for root, dirs, files in os.walk(folder1_path):
        for filename in files:
            # Check if filename contains "_bioc"
            if file_type not in filename:
                continue

            # Get paths for the current files in both folders
            stable_file_path = os.path.join(root, filename)
            new_file_path = os.path.join(folder2_path, F"PMC{filename}")

            # Check if the corresponding file exists in folder2_path
            if os.path.exists(new_file_path):
                # Open both files for comparison
                with open(stable_file_path, 'r', encoding="utf-8") as f1, open(new_file_path, 'r',
                                                                               encoding="utf-8") as f2:
                    lines1 = f1.readlines()
                    lines2 = f2.readlines()

                    # List comprehension to find line numbers with differences
                    different_lines = [i for i, (line1, line2) in enumerate(zip(lines1, lines2)) if
                                       re.sub(r"\s+", "", line1, flags=re.UNICODE) != re.sub(r"\s+", "", line2,
                                                                                             flags=re.UNICODE) and
                                       not any(x for x in lines_to_ignore if x in line1)]

                    # Filter out false positives
                    false_positives = different_lines
                    different_lines = []
                    for i in range(len(false_positives)):
                        if "[PMC free article]" not in lines1[false_positives[i]] and "[PMC free article]" in lines2[
                            false_positives[i]]:
                            continue
                        else:
                            different_lines.append(false_positives[i])

                    # If differences found, add filename to different_files list
                    if different_lines:
                        different_files.append(filename)

    # Log filenames with differences and total count
    logging.log(level=logging.INFO, msg=F"{len(different_files)} files differed.")
    if different_files:
        logging.log(level=logging.INFO, msg="\n".join(different_files))


def main():
    journals = [x for x in os.listdir("../../configs") if x.startswith("config_") and x.endswith(".json")]
    folder1_path = 'StableOutput'
    folder2_path = 'NewOutput'
    lines_to_ignore = ["\"date\":", "\"offset\":", "\"inputfile\":"]
    for journal in journals:
        journal = journal.replace("config_", "").replace(".json", "")
        stable_journal_path = os.path.join(folder1_path, journal)
        new_journal_path = os.path.join(folder2_path, journal)
        logging.log(level=logging.INFO, msg=F"Scanning main text output for {journal} articles.")
        scan_files(stable_journal_path, new_journal_path, journal, lines_to_ignore, file_type="_bioc.json")
        logging.log(level=logging.INFO, msg=F"Scanning tables output for {journal} articles.")
        scan_files(stable_journal_path, new_journal_path, journal, lines_to_ignore, file_type="_tables.json")
        logging.log(level=logging.INFO, msg=F"Scanning abbreviations output for {journal} articles.")
        scan_files(stable_journal_path, new_journal_path, journal, lines_to_ignore, file_type="_abbreviations.json")


if __name__ == "__main__":
    main()
