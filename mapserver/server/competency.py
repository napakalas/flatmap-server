#===============================================================================
#
#  Flatmap server
#
#  Copyright (c) 2019-25  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#===============================================================================
"""

See ../docs/competency.rst

"""
#===============================================================================

from litestar import get, post, Request, Router
from litestar.openapi.spec import Example
from litestar.params import Parameter, Body
from typing import Annotated

#===============================================================================

from ..competency import query, query_definition, query_definitions, get_competency_schema_info

from ..competency.definition import QueryDefinitionDict, QueryDefinitionSummary
from ..competency.definition import QueryRequest, QueryError, QueryResults

#===============================================================================

QueryIdParameter = Annotated[
    str,
    Parameter(
        description=(
            'The ID of the competency query. '
            'See [GET /competency/queries/](#get-/competency/queries) for the list of available queries.'
        ),
        examples=[Example(summary='Example query ID', value='1',)],
    ),
]

QueryRequestBody = Annotated[
    QueryRequest,
    Body(
        description='The competency query ID and the parameter values required by that query.',
        schema_extra={
            'example': {
                'query_id': '1',
                'parameters': [
                    {
                        'column': 'feature_id',
                        'value': 'UBERON:0001759',
                    },
                    {
                        'column': 'source_id',
                        'value': 'sckan-2026-02-11',
                    },
                ],
            }
        },
    ),
]

#===============================================================================

@get(
    'queries',
    description=('Retrieve all available competency query definitions.')
)
async def competency_query_definitions(request: Request) -> list[QueryDefinitionSummary]:
#=======================================================================================
    return await query_definitions(request)

@get(
    'queries/{query_id:str}',
    description='Retrieve a competency query definition by ID.'
)
async def competency_query_definition(query_id: QueryIdParameter, request: Request) -> QueryDefinitionDict:
#==========================================================================================================
    return await query_definition(query_id, request)

@post(
    'query/',
    description=(
        'Execute a competency query. '
        'The required parameters depend on the selected query_id. '
        'See [GET /competency/queries/{query_id}](#get-/competency/queries/-query_id-) for parameter definitions. '
        'See [GET /competency/queries/](#get-/competency/queries) for the list of available queries.'
    )
)
async def competency_query(data: QueryRequestBody, request: Request) -> QueryResults|QueryError:
#===========================================================================================
    result = await query(data, request)
    if 'error' in result:
        request.logger.warning(result["error"])
    return result

@get(
    'schema-version',
    description=('Retrieve version details for the competency schema.')
)
async def competency_schema_version(request: Request) -> dict[str, str|None]:
#==========================================================================
    return await get_competency_schema_info(request.app)

#===============================================================================
#===============================================================================

competency_router = Router(
    path="/competency",
    route_handlers=[
        competency_query,
        competency_schema_version,
        competency_query_definition,
        competency_query_definitions,
    ]
)

#===============================================================================
