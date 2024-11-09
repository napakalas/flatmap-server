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

import logging
import os
import typing

#===============================================================================

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.logging import BaseLoggingConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import RapidocRenderPlugin
from litestar.types import GetLogger, Logger

#===============================================================================

from ..knowledge import KnowledgeStore
from ..settings import settings
from .. import __version__

from .annotator import annotator_router
from .connectivity import connectivity_router
from .dashboard import dashboard_router
from .flatmap import flatmap_router
from .knowledge import knowledge_router
from .maker import maker_router, initialise as init_maker, terminate as end_maker
from .viewer import viewer_router

#===============================================================================

# A simple logging configuration class so that Litestar will use the Python
# logger (called ``litestar``) that was configured in ``__main__.py``.

class LoggingConfig(BaseLoggingConfig):
    def configure(self) -> GetLogger:
        return typing.cast(GetLogger, logging.getLogger)

    @staticmethod
    def set_level(logger: Logger, level: int) -> None:
        logger.setLevel(level)

#===============================================================================

def initialise(app: Litestar):
    if settings['MAP_VIEWER'] and not os.path.exists(settings['FLATMAP_VIEWER']):
        exit(f'Missing {settings["FLATMAP_VIEWER"]} directory -- set FLATMAP_VIEWER environment variable to the full path')

    settings['LOGGER'] = logger = logging.getLogger('litestar')
    logger.info(f'Starting flatmap server version {__version__}')

    if not settings['MAPMAKER_TOKENS']:
        logger.warning('No bearer tokens defined')

    # Try opening our knowledge base
    knowledge_store = KnowledgeStore(settings['FLATMAP_ROOT'], create=True)
    if knowledge_store.error is not None:
        logger.error('{}: {}'.format(knowledge_store.error, knowledge_store.db_name))
    knowledge_store.close()

    init_maker()

#===============================================================================

def terminate(app: Litestar):
    end_maker()
    settings['LOGGER'].info(f'Shutdown flatmap server...')

#===============================================================================

route_handlers = [
    dashboard_router,
    annotator_router,
    connectivity_router,
    flatmap_router,
    knowledge_router,
    maker_router,
]

if settings['MAP_VIEWER']:
    route_handlers.append(viewer_router)

app = Litestar(
    route_handlers=route_handlers,
    cors_config=CORSConfig(allow_origins=["*"]),
    openapi_config=OpenAPIConfig(
        title="Flatmap Server Web API",
        version=__version__,
        render_plugins=[RapidocRenderPlugin()],
    ),
    on_startup=[initialise],
    on_shutdown=[terminate],
    logging_config=LoggingConfig()
)

#===============================================================================
#===============================================================================