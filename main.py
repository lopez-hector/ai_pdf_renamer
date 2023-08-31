"""
    create a script that will read the first page of a pdf and rename the file to title plus last author. Title will be truncated.
"""
import argparse
import json, re
import shutil
from pathlib import Path
from pprint import pprint
from typing import Union, Dict
import os
import pypdf

from utils import load_hashes_from_file, calculate_hash, save_hashes_to_file

OpenAIResponse = str


def open_ai_get_pdf_info(text_split) -> OpenAIResponse:
    import openai
    system_prompt = """
        I am an assistant that processes text from a pdf scientific article extract key information. 
        I will identify the last author of the scientific article, the title of the scientific article, and the year of publication: I will return it in JSON format. Name will be formatted as last_first (no commas). All text must be valid JSON and contain no non-alphanumeric characters.
        Example: 
        
        {"last_author": "last_first", "title": "title", "year": year_of_publication}
        """
    user_prompt = f"""
        Please extract the year, title, and last contributing author (corresponding author) from this text: ```{text_split}```.
        If you cannot extract the information return: None.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],

    )
    return response['choices'][0]['message']['content']


def read_pdf(filepath: Union[str, Path]):
    if isinstance(filepath, Path):
        pdf_file = filepath.open('rb')
    else:
        pdf_file = open(filepath, 'rb')

    pdfReader = pypdf.PdfReader(pdf_file)
    print('-' * 50)
    print(pdfReader.metadata)
    print('-' * 50)
    for i, page in enumerate(pdfReader.pages):
        yield page.extract_text()


def get_pdf_info(filepath: Union[str, Path]) -> Union[Dict, None]:
    """
        1. Grab directory pdfs
        2. read pdf
        3. use gpt to extract the title and last author
        4. reaname each pdf with the titel_author.pdf
    :return:
    """
    info = None

    for i, page in enumerate(read_pdf(filepath)):
        print('*'*5)
        print('*'*5)
        print(filepath, page[:100])
        print('*' * 5)
        print('*' * 5)
        if page:
            info = open_ai_get_pdf_info(text_split=page)

            if 'none' not in info.lower():
                break
            elif i > 1:
                break
        else:
            print('no content')

    try:
        return json.loads(info)
    except json.decoder.JSONDecodeError:
        return None
    except TypeError:
        return None


def main(dirs: Path, rename_file: bool = False, force: bool=False):
    root_dir = Path(__file__).resolve().parent
    hashes_file_path = root_dir / 'hashes.pkl'
    processed_hashes = load_hashes_from_file(hashes_file_path)

    for file in dirs.iterdir():

        if file.is_file() and file.name[-3:] == 'pdf':
            # check if its already processed
            pdf_hash = calculate_hash(file)
            if pdf_hash in processed_hashes and not force:
                continue

            info: Dict = get_pdf_info(file)

            if info is None:
                print(f'skipping {file.name}')
                continue  # skip this file

            title = str(info['year']) + '_' + info['title'][:30].replace(" ", "").replace(':', '-') + '_' + info['last_author'].replace(' ', '') + '.pdf'
            print('title')
            print(title)
            new_file_path = file.with_name(title)
            if rename_file is False:
                print('copying')
                shutil.copy(file, new_file_path)
            else:
                print('renaming')
                file.rename(new_file_path)

            processed_hashes.add(pdf_hash)
            save_hashes_to_file(hashes_file_path, processed_hashes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process pdf files and rename.")
    parser.add_argument("--directory", type=str, help="Directory you want to process.")
    parser.add_argument('--rename', action='store_true', help='Rename file')
    parser.add_argument('-f', '--force_process', action='store_true', help='force_process_files')

    args = parser.parse_args()
    directory_to_rename = Path(args.directory)
    main(directory_to_rename, rename_file=args.rename, force=args.force_process)
