import pytest
from utility import cq_request, assert_valid_query_response, SCKAN_VERSION

base_query = {
    'query_id': '4',
    'parameters': [
        {'column': 'path_id', 'value': 'ilxtr:neuron-type-aacar-11'},
        {'column': 'taxon_id', 'value': 'NCBITaxon:9615'}
    ]
}

def test_sckan():
    query = {**base_query, 'parameters': base_query['parameters'] + [{'column': 'source_id', 'value': SCKAN_VERSION}]}
    expected_evidence_ids = [
        'PMID:27783854',
        'https://doi.org/10.5281/zenodo.14042941'
    ]
    response = cq_request(query)
    assert_valid_query_response(
        response,
        expected_num_keys=2,
        expected_num_values=2,
        expected_column_values={'evidence_id': expected_evidence_ids}
    )
