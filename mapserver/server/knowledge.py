#===============================================================================
#
#  Flatmap server
#
#  Copyright (c) 2019-2024  David Brooks
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

from dataclasses import dataclass
import os
from typing import Annotated, Optional

#===============================================================================

from litestar import get, MediaType, post, Request, Router
from litestar.params import Body
from litestar.response import File

#===============================================================================

from ..knowledge import KnowledgeStore
from ..knowledge.hierarchy import CACHED_SPARC_HIERARCHY
from ..settings import settings

#===============================================================================
#===============================================================================

@dataclass
class QueryData:
    sql: Annotated[
        str,
        Body(description='A read-only SQLite SQL statement to execute against the knowledge store.'),
    ]
    params: Annotated[
        Optional[list[str]],
        Body(description='Values bound to positional `?` placeholders in `sql`, in order.'),
    ] = None

@dataclass
class KnowledgeSourcesResponse:
    sources: list[str]

@dataclass
class ForeignKeyDefinition:
    column: str
    to_table: str
    to_column: str

@dataclass
class ColumnDefinition:
    name: str
    type: str
    primary_key: bool
    nullable: bool

@dataclass
class TableDefinition:
    name: str
    columns: list[ColumnDefinition]
    foreign_keys: list[ForeignKeyDefinition]

@dataclass
class DatabaseSchemaResponse:
    tables: list[TableDefinition]

#===============================================================================
#===============================================================================

KnowledgeQueryBody = Annotated[
    QueryData,
    Body(
        description='SQL statement and positional parameter values for a knowledge-store query.',
        schema_extra={
            'example': {
                'sql': 'SELECT value FROM metadata WHERE name = ?',
                'params': ['schema_version'],
            },
        },
    ),
]

def query_knowledge(sql: str, params: list[str]) -> dict:
#========================================================
    knowledge_store = KnowledgeStore(settings['FLATMAP_ROOT'])
    result = knowledge_store.query(sql, params) if knowledge_store else {
                'error': 'Knowledge Store not available'
             }
    knowledge_store.close()
    return result

def get_knowledge_sources() -> list[str]:
#========================================
    knowledge_store = KnowledgeStore(settings['FLATMAP_ROOT'])
    sources = knowledge_store.knowledge_sources() if knowledge_store else []
    knowledge_store.close()
    return sources

def get_database_schema() -> DatabaseSchemaResponse:
#===================================================
    """
    Returns the flatmap server's knowledge base schema.
    """
    tables_result = query_knowledge(
        "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';",
        []
    )
    if "error" in tables_result or "values" not in tables_result:
        return DatabaseSchemaResponse(tables=[])

    table_names = [row[0] for row in tables_result["values"]]
    schema_tables = []
    for table_name in table_names:
        # Fetch Foreign Keys via table-valued function syntax
        # Format returns: (id, seq, table, from, to, on_update, on_delete, match)
        fk_sql = f"SELECT * FROM pragma_foreign_key_list('{table_name}');"
        fk_result = query_knowledge(fk_sql, [])
        foreign_keys = [
            ForeignKeyDefinition(column=row[3], to_table=row[2], to_column=row[4])
            for row in fk_result["values"] if row is not None
        ] if "values" in fk_result else []
        # Fetch Columns via table-valued function syntax
        # Format returns: (cid, name, type, notnull, dflt_value, pk)
        col_sql = f"SELECT name, type, pk, [notnull] FROM pragma_table_info('{table_name}');"
        col_result = query_knowledge(col_sql, [])
        columns = [
            ColumnDefinition(
                name=row[0],
                type=row[1] if row[1] else "TEXT",
                primary_key=bool(row[2]),
                nullable=not bool(row[3])
            )
            for row in col_result["values"]
        ] if "values" in col_result else []

        schema_tables.append(TableDefinition(
            name=table_name,
            columns=columns,
            foreign_keys=foreign_keys
        ))
    return DatabaseSchemaResponse(tables=schema_tables)

#===============================================================================
#===============================================================================

@post(
    'query/',
    description=(
        'Execute a read-only SQL query against the flatmap knowledge store. '
        'Use [GET /knowledge/schema](#get-/knowledge/schema) to inspect the available tables and columns.'
    ),
)
async def knowledge_query(data: KnowledgeQueryBody, request: Request) -> dict:
#====================================================================
    """
    Query the flatmap server's knowledge base.

    :<json string sql: SQL code to execute
    :<jsonarr string params: any parameters for the query

    :>json array(string) keys: column names of result values
    :>json array(array(string)) values: result data rows
    :>json string error: any error message
    """
    result = query_knowledge(data.sql, data.params if data.params is not None else [])
    if 'error' in result:
        request.logger.warning(f'SQL: {result["error"]}')
    return result

@get(
    'sources',
    description='List the available SCKAN knowledge-source versions, newest first.',
)
async def knowledge_sources() -> KnowledgeSourcesResponse:
#=========================================================
    """
    Return the knowledge sources available in the server's knowledge store.

    :>json array(string) sources: a list of knowledge sources. The list is
                                  in descending order, with the most recent
                                  source at the beginning
    """
    sources = get_knowledge_sources()
    return KnowledgeSourcesResponse(sources)

@get(
    'sparcterms',
    description='Download the cached SPARC anatomical hierarchy as JSON.',
)
async def knowledge_sparcterms() -> File:
#========================================
    filename = os.path.join(settings['FLATMAP_ROOT'], CACHED_SPARC_HIERARCHY)
    return File(path=filename, media_type=MediaType.JSON)

@get(
    'schema-version',
    description='Return the schema version of the flatmap knowledge store.',
)
async def knowledge_schema_version(request: Request) -> dict:
#============================================================
    """
    :>json number version: the version of the store's schema
    """
    result = query_knowledge('select value from metadata where name=?', ['schema_version'])
    if 'error' in result:
        request.logger.warning(f'SQL: {result["error"]}')
    return {'version': result['values'][0][0]}

@get(
    'schema',
    description='Return all knowledge-store tables, columns, and foreign-key relationships.',
)
async def knowledge_schema() -> DatabaseSchemaResponse:
#======================================================
    """
    Return the complete relational schema blueprint of the database.
    """
    return get_database_schema()

#===============================================================================
#===============================================================================

knowledge_router = Router(
    path="/knowledge",
    route_handlers=[
        knowledge_query,
        knowledge_schema,
        knowledge_schema_version,
        knowledge_sources,
        knowledge_sparcterms
    ]
)

#===============================================================================
