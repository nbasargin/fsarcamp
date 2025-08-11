"""
Shared utility functions for F-SAR campaigns.
"""

from xml.etree import ElementTree


def get_flight_and_pass_ids(pass_name):
    """
    Extract flight and pass IDs (numbers) from pass name.
    Pass names are expected to follow the format "yynnnnnnffpp", where "yy" is the year,
    "nnnnnn" is the campaign code, "ff" is the flight ID, and "pp" is the pass ID.
    Example pass names: "14cropex0203", "22hterra0104"
    Returns flight and pass IDs, as two-letter strings
    """
    flight_id, pass_id = pass_name[-4:-2], pass_name[-2:]
    return flight_id, pass_id


def parse_xml_parameters(xml_path):
    """
    Helper function to parse radar parameters from XML files.
    """
    params = dict()
    e = ElementTree.parse(xml_path).getroot()
    for elem in e.findall(".//parameter"):
        if elem.find("datatype").text not in ["pointer", "struct"]:
            params[elem.get("name")] = elem.find("value").text
    return params
