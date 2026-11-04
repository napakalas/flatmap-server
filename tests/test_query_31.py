import pytest
from utility import cq_request, assert_valid_query_response, SCKAN_VERSION

base_query = {
    'query_id': '31',
    'parameters': []
}

SCKAN_BOUNDARY = 'sckan-2026-02-11'

expected_cell_ids = {
        'cell_id': [
            'ilx:npo/uris/neurons/915',
            'ilx:npo/uris/neurons/920'
        ]
    }

def test_sckan():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': SCKAN_VERSION}]}
    response = cq_request(query)

    assert_valid_query_response(
        response,
        minimums_rows = 0 if SCKAN_BOUNDARY <= SCKAN_VERSION else 5,
        expected_column_values = {} if SCKAN_BOUNDARY <= SCKAN_VERSION else expected_cell_ids,
    )

