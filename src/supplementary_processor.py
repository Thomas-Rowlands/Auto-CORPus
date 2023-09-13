import os.path

import file_extension_analysis
import pdf_extractor
import word_extractor
import excel_extractor

word_extensions = [".doc", ".docx"]
spreadsheet_extensions = [".csv", ".xls", ".xlsx"]
supplementary_types = word_extensions + spreadsheet_extensions + [".pdf"]


def __extract_word_data(locations=None, file=None):
    """
    Extracts data from Word documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of Word documents.
            The keys are file extensions associated with Word documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of Word documents with the extension.
                - 'locations' (list): A list of paths to the locations of Word documents.

    Returns:
        None

    """
    if locations:
        word_locations = [locations[x]["locations"] for x in word_extensions if locations[x]["locations"]]
        temp = []
        for x in word_locations:
            if not type(x) == list:
                temp.append(x)
            else:
                for y in x:
                    temp.append(y)
        word_locations = temp
        # Iterate over the file locations of Word documents
        for x in word_locations:
            # Process the Word document using a custom word_extractor
            word_extractor.process_word_document(x)

    if file:
        word_extractor.process_word_document(file)


def __extract_pdf_data(locations=None, file=None):
    """
    Extracts data from PDF documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of PDF documents.
            The keys are file extensions associated with PDF documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of PDF documents with the extension.
                - 'locations' (list): A list of paths to the locations of PDF documents.

    Returns:
        None

    """
    if locations:
        pdf_locations = locations[".pdf"]["locations"]
        # Iterate over the file locations of PDF documents
        for x in pdf_locations:
            # Process the PDF document using a custom pdf_extractor
            pdf_extractor.process_pdf(x)
    if file:
        pdf_extractor.process_pdf(file)


def __extract_spreadsheet_data(locations=None, file=None):
    """
    Extracts data from Spreadsheet documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of Spreadsheet documents.
            The keys are file extensions associated with Spreadsheet documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of Spreadsheet documents with the extension.
                - 'locations' (list): A list of paths to the locations of Spreadsheet documents.

        file (str): A string containing a spreadsheet file path to process.

    Returns:
        None

    """
    if locations:
        spreadsheet_locations = [locations[x]["locations"] for x in spreadsheet_extensions]
        # Iterate over the file locations of Spreadsheet documents
        for x in spreadsheet_locations:
            # Process the PDF document using a custom excel_extractor
            excel_extractor.process_spreadsheet(x)
    if file:
        excel_extractor.process_spreadsheet(file)


def process_supplementary_files(supplementary_files):
    """
    Processes input list of file paths as supplementary data.

    Args:
        supplementary_files (list): List of file paths
    """
    for file in supplementary_files:
        if not os.path.exists(file) or os.path.isdir(file):
            continue

        # Extract data from Word files if they are present
        if [1 for x in word_extensions if file.endswith(x)]:
            __extract_word_data(file=file)

        # Extract data from PDF files if they are present
        elif file.endswith("pdf"):
            __extract_pdf_data(file=file)

        # Extract data from spreadsheet files if they are present
        elif [1 for x in spreadsheet_extensions if file.endswith(x)]:
            __extract_spreadsheet_data(file=file)


def generate_file_report(input_directory):
    """
    Generates a file report based on the file extensions present in the input directory.

    Args:
        input_directory (str): The path to the input directory.

    Returns:
        None or dict: Returns None if no file extensions are found in the input directory.
        If file extensions are found, returns a dictionary containing extracted data based on
        specific file types.

    """
    if not os.path.exists(input_directory) or not os.path.isdir(input_directory):
        return None
    file_extensions = file_extension_analysis.get_file_extensions(input_directory)
    # Check if no file extensions are found
    if not file_extensions:
        return None
    # Check if PDF files are present
    pdf_present = "pdf" in file_extensions.keys()
    # Check if Word files are present
    word_present = True if any([x for x in file_extensions.keys() if x in word_extensions]) else False
    # Check if spreadsheet files are present
    spreadsheet_present = True if any([x for x in file_extensions.keys() if x in spreadsheet_extensions]) else False
    # Extract data from Word files if they are present
    if word_present:
        word_locations = {x: file_extensions[x] for x in word_extensions}
        __extract_word_data(word_locations)
    # Extract data from PDF files if they are present
    if pdf_present:
        pdf_locations = {".pdf": file_extensions[".pdf"]}
        __extract_pdf_data(pdf_locations)
    # Extract data from spreadsheet files if they are present
    if spreadsheet_present:
        spreadsheet_locations = {x: file_extensions[x] for x in spreadsheet_extensions}
        __extract_spreadsheet_data(spreadsheet_locations)
    return True
