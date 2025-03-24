import logging
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from math import ceil
from pathlib import Path
from typing import cast

import lxml.etree as etree
from lxml.etree import _Element as Element


class DataVaultTypes(Enum):
    hub = "h"
    link = "l"
    satellite = "s"


class AnchorTypes(Enum):
    anchor = "a"
    tie = "t"
    attribute = "r"


SYSTEM_COLS = [
    "source_id",
    "load_dttm",
]


@dataclass
class Column:
    flag: str
    name: str


@dataclass
class Table:
    name: str
    type: DataVaultTypes | AnchorTypes
    columns: list[Column]

    @property
    def width(self) -> int:
        return 180

    @property
    def height(self) -> int:
        return ceil(37.5 * len(self.columns))

    def table_def(self, x: int, y: int) -> str:
        return """
        <mxCell id="{table_name}" value="{table_name}" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />
        </mxCell>
        """.format(
            table_name=self.name,
            x=x,
            y=y,
            width=self.width,
            height=self.height,
        )

    def pk_def(self, column: Column) -> str:
        return """
        <mxCell id="{table_name}_{column_name}_container" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=1;" vertex="1" parent="{table_name}">
          <mxGeometry y="30" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="{table_name}_{column_name}_flag" value="{column_flag}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontStyle=1;overflow=hidden;whiteSpace=wrap;html=1;" vertex="1" parent="{table_name}_{column_name}_container">
          <mxGeometry width="30" height="30" as="geometry">
            <mxRectangle width="30" height="30" as="alternateBounds" />
          </mxGeometry>
        </mxCell>
        <mxCell id="{table_name}_{column_name}_column" value="{column_name}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;fontStyle=5;overflow=hidden;whiteSpace=wrap;html=1;" vertex="1" parent="{table_name}_{column_name}_container">
          <mxGeometry x="30" width="150" height="30" as="geometry">
            <mxRectangle width="150" height="30" as="alternateBounds" />
          </mxGeometry>
        </mxCell>
        """.format(
            table_name=self.name,
            column_name=column.name,
            column_flag=column.flag,
        )

    def col_def(self, column: Column) -> str:
        return """
        <mxCell id="{table_name}_{column_name}_container" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;" vertex="1" parent="{table_name}">
          <mxGeometry y="60" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="{table_name}_{column_name}_flag" value="{column_flag}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;editable=1;overflow=hidden;whiteSpace=wrap;html=1;" vertex="1" parent="{table_name}_{column_name}_container">
          <mxGeometry width="30" height="30" as="geometry">
            <mxRectangle width="30" height="30" as="alternateBounds" />
          </mxGeometry>
        </mxCell>
        <mxCell id="{table_name}_{column_name}_column" value="{column_name}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;overflow=hidden;whiteSpace=wrap;html=1;" vertex="1" parent="{table_name}_{column_name}_container">
          <mxGeometry x="30" width="150" height="30" as="geometry">
            <mxRectangle width="150" height="30" as="alternateBounds" />
          </mxGeometry>
        </mxCell>
        """.format(
            table_name=self.name,
            column_name=column.name,
            column_flag=column.flag,
        )

    def dump_xml(self, x: int, y: int) -> str:
        result = ""
        pk_cols = [self.pk_def(c) for c in self.columns if c.flag == "PK"]
        normal_cols = [self.col_def(c) for c in self.columns if c.flag == ""]
        sys_cols = [self.col_def(c) for c in self.columns if c.flag == "SYS"]

        result += self.table_def(x, y)
        result += reduce(lambda a, b: a + b, pk_cols)
        result += reduce(lambda a, b: a + b, normal_cols) if normal_cols else ""
        result += reduce(lambda a, b: a + b, sys_cols)
        return result


def _xpath_to_elements(search_result: "etree._XPathObject") -> list[Element]:
    return cast(list[Element], [r for r in search_result])  # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType]


def prettyprint(element: Element):
    xml = etree.tostring(element, pretty_print=True)
    print(xml.decode(), end="")


def load(xml_file: Path) -> Element:
    tree = etree.parse(xml_file)
    root: Element = tree.getroot()
    prettyprint(root)
    return root


def find_tables(root: Element, data_vault_type: DataVaultTypes) -> list[Element]:
    result = _xpath_to_elements(
        root.xpath('//mxCell[starts-with(@value, "{}_")]'.format(data_vault_type.value))
    )
    logging.info(
        "Found tables of type {}: {}".format(
            data_vault_type.name,
            "; ".join([t.get("value") or "`name not found`" for t in result]),
        )
    )
    return result


def parse_table(root: Element, table: Element, table_type: DataVaultTypes) -> Table:
    parent_id = table.get("id")
    assert parent_id is not None
    column_containers = _xpath_to_elements(
        root.xpath('//mxCell[@parent="{}"]'.format(parent_id))
    )
    table_name = table.get("value")
    assert table_name is not None, "name of table not found"
    columns: list[Column] = []
    for column_container in column_containers:
        column_container_id = column_container.get("id")
        assert column_container_id is not None
        column_innards = _xpath_to_elements(
            root.xpath('//mxCell[@parent="{}"]'.format(column_container_id))
        )
        match len(column_innards):
            case 1:
                flag = ""
                col_name = column_innards[0].get("value") or "`name not found`"
            case 2:
                first_val = column_innards[0].get("value") or ""
                second_val = column_innards[1].get("value") or ""

                FLAGS = ["", "FK", "PK"]
                if first_val.upper() in FLAGS:
                    flag = first_val.upper()
                    col_name = second_val
                elif second_val.upper() in FLAGS:
                    flag = second_val.upper()
                    col_name = first_val
                elif len(first_val) < len(first_val):
                    flag = first_val.upper()
                    col_name = second_val
                else:
                    flag = second_val.upper()
                    col_name = first_val
            case _:
                raise ValueError(
                    "Unexpected `{}`'s children count of {}".format(
                        column_container_id, len(column_innards)
                    )
                )

        flag = flag if col_name not in SYSTEM_COLS else "SYS"

        logging.info(
            "Found columns in {: <30}: {: <3} {}".format(
                table_name,
                flag,
                col_name,
            )
        )
        columns.append(Column(flag, col_name))

    return Table(name=table_name, type=table_type, columns=columns)


def system_columns():
    return [Column("SYS", c) for c in SYSTEM_COLS]


def convert_dv_to_anchor(table: Table) -> list[Table]:
    new_tables: list[Table] = []
    match table.type:
        case DataVaultTypes.hub:
            pk = [c for c in table.columns if c.flag == "PK"]
            ext_key = [c for c in table.columns if c.flag == ""]
            assert len(pk) == 1
            assert len(ext_key) == 1
            new_tables.append(
                Table(
                    name=AnchorTypes.anchor.value + table.name[1:],
                    type=AnchorTypes.anchor,
                    columns=pk + system_columns(),
                )
            )
            new_tables.append(
                Table(
                    name=AnchorTypes.attribute.value + table.name[1:] + "_business_key",
                    type=AnchorTypes.attribute,
                    columns=pk + ext_key + system_columns(),
                ),
            )
        case DataVaultTypes.link:
            # My links are already in tie form, I don't use `Transactional Links`
            new_tables.append(
                Table(
                    name=AnchorTypes.tie.value + table.name[1:],
                    type=AnchorTypes.tie,
                    columns=table.columns,
                )
            )
        case DataVaultTypes.satellite:
            pk = [c for c in table.columns if c.flag == "PK"]
            assert len(pk) == 1
            for column in table.columns:
                if column.flag != "":
                    logging.debug(
                        "When generating new table from `{}` skiped column `{}` for flag `{}`".format(
                            table.name, column.name, column.flag
                        )
                    )
                    continue
                new_tables.append(
                    Table(
                        name="{}{}_{}".format(
                            AnchorTypes.attribute.value, table.name[1:], column.name
                        ),
                        type=AnchorTypes.attribute,
                        columns=pk + [column] + system_columns(),
                    )
                )
        case AnchorTypes():
            raise ValueError(
                "Table {} is already anchor type: {}".format(table.name, table.type)
            )

    return new_tables


def save_model(xml_model: str, output: Path):
    prefix = """
    <mxfile host="app.diagrams.net" agent="Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0" version="26.1.1">
        <diagram name="Page-1" id="e56a1550-8fbb-45ad-956c-1786394a9013">
            <mxGraphModel dx="2735" dy="1730" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850" background="none" math="0" shadow="0">
            <root>
                <mxCell id="0" />
                <mxCell id="1" parent="0" />

    """
    suffix = """

            </root>
            </mxGraphModel>
        </diagram>
    </mxfile>
    """
    with open(output, mode="w") as f:
        _ = f.write(prefix)
        _ = f.write(xml_model)
        _ = f.write(suffix)


def dump_model(tables: list[Table]) -> str:
    result = ""

    table_offects: dict[str, tuple[int, int]] = {}
    anchor_pks: dict[str, str] = {}

    X_OFFSET = 50
    Y_OFFSET = 100

    y_next = Y_OFFSET

    for table in tables:
        if table.type != AnchorTypes.anchor:
            continue
        pk = [c for c in table.columns if c.flag == "PK"]
        assert len(pk) == 1
        # Searching for anchor's pk
        anchor_pks[pk[0].name] = "{}_{}_container".format(table.name, pk[0].name)

        # Saving anchor on canvas
        # x offset =  Border offset + current table + next offset
        result += table.dump_xml(X_OFFSET, y_next)
        table_offects[pk[0].name] = (X_OFFSET + table.width + X_OFFSET, y_next)
        # y just moves next
        y_next += table.height + Y_OFFSET

    relations_to_create: list[tuple[str, str]] = []
    for table in tables:
        if table.type == AnchorTypes.anchor:
            continue

        non_anchor_pks = [c for c in table.columns if c.flag == "PK"]
        # Searching for non anchor's pk and marking combo of
        # anchor's pk and non anchor pk for future link
        for pk in non_anchor_pks:
            this_pk = "{}_{}_container".format(table.name, pk.name)
            relations_to_create.append((anchor_pks[pk.name], this_pk))

        # attribute stacked right of anchor
        if table.type == AnchorTypes.attribute:
            pk_name = non_anchor_pks[0].name
            current_offeset = table_offects[pk_name]
            result += table.dump_xml(*current_offeset)
            table_offects[pk_name] = (
                current_offeset[0] + table.width + X_OFFSET,
                current_offeset[1],
            )
        # ties stacked in one spot top left
        elif table.type == AnchorTypes.tie:
            result += table.dump_xml(-150, -150)

    relation_template = """
    <mxCell id="{source}_to_{target}" value="" style="edgeStyle=entityRelationEdgeStyle;fontSize=12;html=1;endArrow=ERmandOne;startArrow=ERmandOne;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="{source}" target="{target}">
        <mxGeometry width="100" height="100" relative="1" as="geometry">
        </mxGeometry>
    </mxCell>
    """
    for source, target in relations_to_create:
        result += relation_template.format(source=source, target=target)

    return result
