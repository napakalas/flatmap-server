import pytest
from utility import cq_request, assert_valid_query_response, MALE_UUID, FEMALE_UUID, RAT_UUID, SCKAN_VERSION

base_query = {
    'query_id': '38',
    'parameters': [
        {'column': 'path_id', 'value': 'ilxtr:neuron-type-aacar-11'}
    ]
}

expected_notes = [
    'changed region/layer pair from aorta (aorta tunica adventiticia) to ascending aorta '
    '(aorta tunica adventiticia) to present the more granular detail.'
]

# a cell precision with two curator notes
cell_query = {
    'query_id': '38',
    'parameters': [
        {'column': 'path_id', 'value': 'npokb:1059'}
    ]
}

expected_cell_notes = [
    'E12 tamoxifen for SA1, postnatal tamoxifen for field',
    'see Figure 1G of https://doi.org/10.1038/s42003-025-08315-1 for asserted equivalences to Yu et al., 2024'
]

def test_sckan():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': SCKAN_VERSION}]}
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_column_values={'note': expected_notes}
    )

def test_sckan_cell_precision():
    query = {**cell_query, 'parameters': cell_query['parameters'] + [{'column': 'source_id', 'value': SCKAN_VERSION}]}
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_column_values={'note': expected_cell_notes}
    )

def test_human_male_map():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': MALE_UUID}]}
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_column_values={'note': expected_notes}
    )

def test_human_female_map():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': FEMALE_UUID}]}
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_column_values={'note': expected_notes}
    )

def test_rat_map():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': RAT_UUID}]}
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_column_values={'note': expected_notes}
    )
