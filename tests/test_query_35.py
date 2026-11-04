import pytest
from utility import cq_request, assert_valid_query_response, SCKAN_VERSION

base_query = {
    'query_id': '35',
    'parameters': [
        {'column': 'cell_id', 'value': 'ilx:npo/uris/neurons/1063'}
    ]
}

SCKAN_BOUNDARY = 'sckan-2026-02-11'

expected_path_ids = {
        'cell_id': [
            'ilx:npo/uris/neurons/1063',
        ],
        'feature_id': [
            'ILX:0110092',
            'UBERON:0006118',
            'UBERON:0002097',
            'UBERON:0000044',
        ]
    }

def test_sckan():
    query = {**base_query, 'parameters': base_query['parameters'] + [
        {'column': 'source_id', 'value': SCKAN_VERSION}
    ]}
    response = cq_request(query)

    assert_valid_query_response(
        response,
        minimums_rows = 0 if SCKAN_BOUNDARY <= SCKAN_VERSION else 100,
        expected_column_values = {} if SCKAN_BOUNDARY <= SCKAN_VERSION else expected_path_ids,
    )
