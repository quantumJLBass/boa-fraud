import time
from pathlib import Path

from sqlalchemy.exc import IntegrityError

import gs
from services.applogging import logger, section
from settings.settings import i
from utils import *
from utils.useollama import *
from utils.ziptest import *

md_contents = """
---
tags:
- MOCs
entry-taxonomic-rank: family
---
```folder-overview
id: {ID}
folderPath: ""
title: "{folderName} overview"
showTitle: true
depth: 4
style: list
includeTypes:
- folder
- all
disableFileTag: true
sortBy: name
sortByAsc: true
showEmptyFolders: false
onlyIncludeSubfolders: false
storeFolderCondition: true
showFolderNotes: true
disableCollapseIcon: true
```
"""


def render_addresses(address: str):
    """_summary_

    Args:
        address (str): _description_
    """
    addresses_dir = Path(__file__).resolve().parent.parent.parent / "addresses-test"

    try:
        good_address, address_obj = lookup_zipcode(address)
        time.sleep(60)
        folder_path = (
            Path(addresses_dir) / good_address
        )  # Create a path object for the folder
        subfolder = folder_path / "files"
        subfolder.mkdir(parents=True, exist_ok=True)  # Create the directory

        # Create the markdown file inside the folder
        markdown_file_path = folder_path / f"{good_address}.md"
        with markdown_file_path.open("w", encoding="utf-8") as file:
            file.write(md_contents)

        try:
            with gs.write() as writesession:
                # Attempt to insert the address into the database
                writesession.add(address_obj)
                writesession.commit()
                logger.info(f"{i()}✅🏠 ADDRESS INSERTED ----- {folder_path}")
        except IntegrityError:
            with gs.write() as writesession:
                writesession.rollback()
            logger.info(f"{i()}🔄🏠 ADDRESS EXISTS ----- {folder_path}")
            logger.error(f"{traceback.format_exc()}")
        except Exception as e:
            with gs.write() as writesession:
                writesession.rollback()
            logger.error(
                f"{i()}💥🚩 ERROR INSERTING ADDRESS ----- {folder_path}: {str(e)}"
            )
            logger.error(f"{traceback.format_exc()}")

    except Exception as e:
        logger.error(f"💥🚩Error processing {address}: {e}")
        logger.error(f"{traceback.format_exc()}")
    finally:
        logger.info(f"{i()}🏁📁 FINISHED INSERTING ADDRESSES")

    section("📁🏠 INSERTING ADDRESSES 🏠📁", "sea_green2", "center")
