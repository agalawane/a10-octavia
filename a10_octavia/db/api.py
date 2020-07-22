#    Copyright 2019, A10 Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from oslo_config import cfg
from oslo_log import log as logging
from contextlib import contextmanager

import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

Base = sqlalchemy.ext.declarative.declarative_base()


def get_base():
    return Base


def get_engine(url=None):

    if url is None:
        url = CONF.database_connection.connection

    return sqlalchemy.create_engine(url)


def get_session(url=None, **kwargs):
    DBSession = sqlalchemy.orm.sessionmaker(bind=get_engine(url=url))
    return DBSession(**kwargs)


def close_session(session):
    try:
        session.commit()
    finally:
        session.close()


@contextmanager
def magic_session(db_session=None, url=None):
    """Either does nothing with the session you already have or
    makes one that commits and closes no matter what happens
    """

    if db_session is not None:
        yield db_session
    else:
        session = get_session(url, expire_on_commit=False)
        try:
            try:
                yield session
            finally:
                session.commit()
        finally:
            session.close()
