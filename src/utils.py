import os
import re
import unicodedata

import bs4
import networkx as nx


def get_files(base_dir, pattern=r"(.*).html"):
    """
    recursively retrieve all PMC.html files from the directory

    Args: 
        pattern: regex string for finding html file names
        base_dir: base directory string

    Return: 
        file_list: a list of filepath
    """
    file_list = []
    files = os.listdir(base_dir)
    for i in files:
        abs_path = os.path.join(base_dir, i)
        if re.match(pattern, abs_path):
            file_list.append(abs_path)
        elif os.path.isdir(abs_path) & ('ipynb_checkpoints' not in abs_path):
            file_list += get_files(abs_path)
    return file_list


def process_supsub(soup):
    """
    add underscore (_) before all superscript or subscript text

    Args: 
        soup: BeautifulSoup object of html

    """
    # for sup in soup.find_all(['sup', 'sub']):
    for sup in soup.find_all('sub'):
        s = sup.get_text()
        if sup.string is None:
            sup.extract()
        elif re.match('[_-]', s):
            sup.string.replace_with('{} '.format(s))
        else:
            sup.string.replace_with('_{} '.format(s))
    return soup


def process_em(soup):
    """
    remove all emphasized text
    No it doesn't, it just adds a space to it

    Args: 
        soup: BeautifulSoup object of html

    """
    for em in soup.find_all('em'):
        s = em.get_text()
        if em.string is None:
            em.extract()
        else:
            em.string.replace_with('{} '.format(s))
    return soup


def read_mapping_file():
    mapping_dict = {}
    with open('src/IAO_dicts/IAO_FINAL_MAPPING.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            heading = line.split('\t')[0].lower().strip('\n')
            iao_term = line.split('\t')[1].lower().strip('\n')
            if iao_term != '':
                if '/' in iao_term:
                    iao_term_1 = iao_term.split('/')[0].strip(' ')
                    iao_term_2 = iao_term.split('/')[1].strip(' ')
                    if iao_term_1 in mapping_dict.keys():
                        mapping_dict[iao_term_1].append(heading)
                    else:
                        mapping_dict.update({iao_term_1: [heading]})

                    if iao_term_2 in mapping_dict.keys():
                        mapping_dict[iao_term_2].append(heading)
                    else:
                        mapping_dict.update({iao_term_2: [heading]})

                else:
                    if iao_term in mapping_dict.keys():
                        mapping_dict[iao_term].append(heading)
                    else:
                        mapping_dict.update({iao_term: [heading]})
    return mapping_dict


def read_iao_term_to_id_file():
    iao_term_to_no_dict = {}
    with open('src/IAO_dicts/IAO_term_to_ID.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            iao_term = line.split('\t')[0]
            iao_no = line.split('\t')[1].strip('\n')
            iao_term_to_no_dict.update({iao_term: iao_no})
    return iao_term_to_no_dict


def config_anchors(value):
    if not value.startswith("^"):
        value = F"^{value}"
    if not value.endswith("$"):
        value = F"{value}$"
    return value


def config_attr_block(block):
    ret = {}
    for key in block:
        if isinstance(block[key], list):
            ret[key] = [re.compile(config_anchors(x)) for x in block[key]]
        elif isinstance(block[key], str):
            ret[key] = re.compile(config_anchors(block[key]))
    return ret


def config_attrs(attrs):
    ret = []
    if isinstance(attrs, list):
        for attr in attrs:
            ret.extend(config_attr_block(attr))
    elif isinstance(attrs, dict):
        ret = config_attr_block(attrs)
    else:
        quit(F"{attrs} must be a dict or a list of dicts")
    return ret


def config_tags(tags):
    ret = []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str):
                ret.append(re.compile(config_anchors(tag)))
            else:
                quit(F"{tags} must be a string or list of strings")
    elif isinstance(tags, str):
        ret.append(re.compile(config_anchors(tags)))
    else:
        quit(F"{tags} must be a string or list of strings")
    return ret


def parse_configs(definition):
    bs_attrs = {
        "name": [],
        "attrs": []
    }
    if "tag" in definition:
        bs_attrs['name'] = config_tags(definition['tag'])
    if "attrs" in definition:
        bs_attrs['attrs'] = config_attrs(definition['attrs'])
    return bs_attrs


def handle_defined_by(config, soup):
    """
    node is a bs4 object of a single result derived from bs4.find_all()
    data is an object where the results from the config "data" sections is housed. The key is the name of the data
    section and the values are all matches found within any of the main matches which match the current data section
    definition. The values are the response you get from get_text() on any found nodes, not the nodes themselves.

    Args:
        config: config file section used to parse
        soup: soup section to parse
    Returns:
        list of bs4 objects, each object being a matching node.
        bs4 object template:
        {
            node: bs4Object,
            data:   {
                        key: [values]
                    }
        }
    """
    if "defined-by" not in config:
        quit(F"{config} does not contain the required 'defined-by' key.")
    matches = []
    seen_text = []
    for definition in config['defined-by']:
        bs_attrs = parse_configs(definition)
        new_matches = soup.find_all(bs_attrs['name'], bs_attrs['attrs'])
        for match in new_matches:
            if match.get_text() in seen_text:
                continue
            else:
                seen_text.append(match.get_text())
                matches.append(match)
    return matches


def handle_not_tables(config, soup):
    responses = []
    matches = handle_defined_by(config, soup)
    if "data" in config:
        for match in matches:
            response_addition = {
                "node": match
            }
            for ele in config['data']:
                seen_text = set()
                for definition in config['data'][ele]:
                    bs_attrs = parse_configs(definition)
                    new_matches = match.find_all(bs_attrs['name'], bs_attrs['attrs'])
                    if new_matches:
                        response_addition[ele] = []
                    for newMatch in new_matches:
                        if newMatch.get_text() in seen_text:
                            continue
                        else:
                            response_addition[ele].append(newMatch.get_text())
            responses.append(response_addition)
    else:
        for match in matches:
            response_addition = {
                "node": match
            }
            responses.append(response_addition)
    return responses


def get_data_element_node(config, soup):
    config = {
        "defined-by": config
    }
    return handle_defined_by(config, soup)


def navigate_contents(item):
    value = ""
    if isinstance(item, bs4.element.NavigableString):
        value += unicodedata.normalize("NFKD", item)
    if isinstance(item, bs4.element.Tag):
        if item.name == "sup" or item.name == "sub":
            value += "<" + item.name + ">"
            for childItem in item.contents:
                value += navigate_contents(childItem)
            value += "</" + item.name + ">"
        else:
            for childItem in item.contents:
                value += navigate_contents(childItem)
    return value


def handle_tables(config, soup):
    responses = []
    matches = handle_defined_by(config, soup)
    text_data = [
        "caption",
        "title",
        "footer"
    ]
    if "data" in config:
        for match in matches:
            response_addition = {
                "node": match,
                "title": "",
                "footer": "",
                "caption": ""
            }
            for ele in config['data']:
                if ele in text_data:
                    seen_text = set()
                    for definition in config['data'][ele]:
                        bs_attrs = parse_configs(definition)
                        new_matches = match.find_all(bs_attrs['name'], bs_attrs['attrs'])
                        if new_matches:
                            response_addition[ele] = []
                        for newMatch in new_matches:
                            if newMatch.get_text() in seen_text:
                                continue
                            else:
                                value = ""
                                for item in newMatch.contents:
                                    value += navigate_contents(item)
                                    # clean the cell
                                value = value.strip().replace('\u2009', ' ')
                                value = re.sub(r"</?span[^>\n]*>?|<hr/>?", "", value)
                                value = re.sub(r"\\n", "", value)
                                response_addition[ele].append(value)
            responses.append(response_addition)
    else:
        for match in matches:
            response_addition = {
                "node": match
            }
            responses.append(response_addition)
    return responses


def assign_heading_by_dag(paper):
    g = nx.read_graphml('src/DAG_model.graphml')
    new_mapping_dict = {}
    mapping_dict_with_dag = {}
    iao_term_to_no_dict = read_iao_term_to_id_file()
    previous_section = ""
    next_section = ""
    previous_heading = ""
    next_heading = ""
    for i, heading in enumerate(paper.keys()):
        if not paper[heading]:
            previous_mapped_heading_found = False
            i2 = 1
            while not previous_mapped_heading_found:
                if i - i2 > len(list(paper.keys())):
                    previous_mapped_heading_found = True
                    previous_section = "Start of the article"
                else:
                    previous_heading = list(paper.keys())[i - i2]
                    if paper[previous_heading]:
                        previous_mapped_heading_found = True
                        previous_section = paper[previous_heading]
                    else:
                        i2 += 1

            next_mapped_heading_found = False
            i2 = 1
            while not next_mapped_heading_found:
                if i + i2 >= len(list(paper.keys())):
                    next_mapped_heading_found = True
                    next_section = "End of the article"
                else:
                    next_heading = list(paper.keys())[i + i2]
                    if paper[next_heading]:
                        next_mapped_heading_found = True
                        next_section = paper[next_heading]
                    else:
                        i2 += 1

            if previous_section != "Start of the article" and next_section != "End of the article":
                if nx.has_path(g, paper[previous_heading][-1], paper[next_heading][0]):
                    paths = nx.all_shortest_paths(
                        g, paper[previous_heading][-1], paper[next_heading][0], weight='cost')
                    for path in paths:
                        if len(path) <= 2:
                            mapping_dict_with_dag.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_dag.update({heading: path[1:-1]})
                else:
                    new_target = paper[list(paper.keys())[i + i2 + 1]][0]
                    paths = nx.all_shortest_paths(
                        g, paper[previous_heading][-1], new_target, weight='cost')
                    for path in paths:
                        if len(path) == 2:
                            mapping_dict_with_dag.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_dag.update({heading: path[1:-1]})

            if next_section == "End of the article":
                mapping_dict_with_dag.update({heading: [previous_section[-1]]})

            for new_heading in mapping_dict_with_dag.keys():
                new_sec_type = []
                for secType in mapping_dict_with_dag[new_heading]:
                    if secType in iao_term_to_no_dict.keys():
                        mapping_result_id_version = iao_term_to_no_dict[secType]
                    else:
                        mapping_result_id_version = ''
                    new_sec_type.append({
                        "iao_name": secType,
                        "iao_id": mapping_result_id_version
                    })

                new_mapping_dict[new_heading] = new_sec_type
    return new_mapping_dict


def is_number(s):
    """
    check if input string is a number

    Args:
        s: input string

    Returns:
        True/False

    """
    try:
        float(s.replace(',', ''))
        return True
    except ValueError:
        return False


def is_mixed_data_type(s):
    """
    check if input string is a mix of number and text

    Args:
        s: input string

    Returns:
        True/False

    """
    if any(char.isdigit() for char in s):
        if any(char for char in s if char.isdigit() is False):
            return True
    return False


def is_text(s):
    """
    check if input string is all text

    Args:
        s: input string

    Returns:
        True/False

    """
    if any(char.isdigit() for char in s):
        return False
    return True
