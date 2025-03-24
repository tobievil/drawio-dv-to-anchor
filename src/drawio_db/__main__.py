import argparse
import logging
from pathlib import Path
from typing import cast

from colorlog import ColoredFormatter
from devtools import pformat

import drawio_db.xml


def parse_args():
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("xml_file", type=Path, help="Path to xml file.")
    args = parser.parse_args()
    result = cast(Path, args.xml_file)
    return result


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = []
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main():
    setup_logger()
    xml_file = parse_args()
    root = drawio_db.xml.load(xml_file)

    converted_tables: list[drawio_db.xml.Table] = []
    for data_vault_type in drawio_db.xml.DataVaultTypes:
        tables_raw = drawio_db.xml.find_tables(root, data_vault_type)
        for table_raw in tables_raw:
            table = drawio_db.xml.parse_table(root, table_raw, data_vault_type)
            converted_table = drawio_db.xml.convert_dv_to_anchor(table)
            converted_tables += converted_table
            logging.info(
                "old table: {}\nnew tables: {}".format(
                    pformat(table, highlight=True),
                    pformat(converted_table, highlight=True),
                )
            )

    result = drawio_db.xml.dump_model(converted_tables)
    drawio_db.xml.save_model(
        result, xml_file.parent / (str(xml_file.stem) + "_anchor.xml")
    )
    logging.info("Dumped: {} tables".format(len(converted_tables)))


if __name__ == "__main__":
    main()
