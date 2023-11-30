from gspread import *
from restful_genie.locations import Locations
from loguru import logger
from typing import Optional, Union
from pathlib import Path
import gspread
from getpaper.download import *
from getpaper.parse import *

class BioTable:

    gc:Client
    sheet: Spreadsheet
    table: Worksheet
    papers: Path
    locations: Locations

    def __init__(self, url: str, sheet: str="Sheet1", locations: Optional[Locations] = None):
        if locations is None:
            cur_file: Path = Path(__file__)
            self.locations = Locations(cur_file.parent.parent.resolve().absolute())
        else:
            self.locations = locations
        self.gc = gspread.service_account(self.locations.service_key)
        self.papers = self.locations.papers
        self.sheet = self.gc.open_by_url(url)
        self.table = self.sheet.worksheet(sheet)

    def get_table(self, name: str):
        return self.sheet.worksheet(name)

    def paper_by_doi(self, doi: str):
        raw_doi = doi.replace("https://doi.org/", "")
        result = try_download(raw_doi, self.papers, True) \
            .map(lambda p: parse_paper(p, self.papers)) \
            .get_or_else_get()
        l = len(result)
        if l == 0:
            logger.warning(f"nothing found for {doi}, returning nothing")
            return ""
        elif l==1:
            return result[0]
        else:
            logger.warning(f"several files were found for {doi}, returning first one")
            return result[0]

    def download_papers(self, ids_column: int = 1,  ids_start: int = 2, into: int = 2):
        doi_ids = self.table.col_values(ids_column)
        for index, doi_id in enumerate(doi_ids[ids_start-1:], start=ids_start):  # using start=1 because spreadsheet indexing starts from 1
            print(f"index is {index}")
            paper_details = self.paper_by_doi(doi_id)
            self.table.update_cell(index, into, paper_details)  # 2 refers to column B
        logger.info(f"finished downloading papers")

    #def read_papers(self, downloaded_columns: int = 2, ids_start: int = 2, into: int = 3):
        #for index, doi_id in enumerate(downloaded_columns[ids_start-1:], start=ids_start):  # using start=1 because spreadsheet indexing starts from 1
        #    parsed = self.
        #    pass
        #    #self.table.update_cell(index, into, paper_details)  # 2 refers to column B
        #logger.info(f"finished parsing papers")
