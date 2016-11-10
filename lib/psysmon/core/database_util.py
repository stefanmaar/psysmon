# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Utility functions to interact with the database.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import sqlalchemy as sqa
import logging
import re

logger_name = __name__
logger = logging.getLogger(logger_name)

def db_table_migration(engine, table, prefix):
    ''' Check if a database table migration is needed and apply the changes.
    '''
    logger.info('Checking if database table %s needs an update.', table.__table__.name)
    table_updated = False
    cur_metadata = sqa.MetaData(engine)
    cur_metadata.reflect(engine)
    if table.__table__.name in cur_metadata.tables.keys():
        # Check for changes between the existing and the new table.
        table_updated = update_db_table(engine = engine,
                                        table = table,
                                        metadata = cur_metadata,
                                        prefix = prefix)
        if not table_updated:
            logger.info('Everything is up-to-date.')
    else:
        # The table is missing in the schema, create it.
        logger.info('The table %s is not existing, create it.', table.__table__.name)
        table.__table__.create()
        table_updated = True

    return table_updated


def update_db_table(engine, table, metadata, prefix):
    ''' Update the table structure to the new schema.
    '''
    table_updated = False
    # Check for added columns.
    new_table = table.__table__
    exist_table = metadata.tables[new_table.name]
    columns_to_add = set(new_table.columns.keys()).difference(set(exist_table.columns.keys()))
    if columns_to_add:
        if not table_updated:
            logger.info('A database table migration is needed.')

        for cur_col in columns_to_add:
            logger.info('Adding column %s to table %s.', cur_col, table.__table__.name)
            add_column(engine = engine,
                       table = table,
                       column = new_table.columns[cur_col],
                       prefix = prefix)

        table_updated = True

    # Check for columns to remove.
    columns_to_remove = set(exist_table.columns.keys()).difference(set(new_table.columns.keys()))
    if columns_to_remove:
        if not table_updated:
            logger.info('A database table migration is needed.')

        for cur_col in columns_to_remove:
            logger.info('Removing column %s from table %s.', cur_col, table.__table__.name)
            remove_column(engine = engine,
                          table = table,
                          column = exist_table.columns[cur_col])

        table_updated = True

    # Check for changed column specifications.
    for cur_name, cur_col in new_table.columns.items():
        if cur_name not in exist_table.columns.keys():
            # The column is not existing in the database. 
            # Might have been deleted. Ignore it.
            continue
        exist_col = exist_table.columns[cur_name]
        # Check for the column type.
        new_type = cur_col.type.compile(engine.dialect)
        exist_type = exist_col.type.compile(engine.dialect)
        if not compare_column_type(new_type, exist_type):
            if not table_updated:
                logger.info('A database table migration is needed.')
            logger.info('Changing the type of column %s from %s to %s.', cur_name, exist_type, new_type)
            change_column_type(engine = engine,
                               table = table,
                               column = cur_col)
            table_updated = True

        # Check for changed foreign keys.
        keys_to_add = cur_col.foreign_keys.difference(exist_col.foreign_keys)
        for cur_key in keys_to_add:
            # Add the foreign key to the column.
            logger.info('Adding foreign key %s to the column %s.', cur_key.target_fullname, cur_name)
            add_foreign_key(engine = engine,
                            table = table,
                            column = cur_col,
                            target = prefix + cur_key.target_fullname)

        keys_to_remove = exist_col.foreign_keys.difference(cur_col.foreign_keys)
        for cur_key in keys_to_remove:
            # Remove the foreign key from the column.
            logger.info('Removing foreign key %s from the column %s.', cur_key.target_fullname, cur_name)
            remove_foreign_key(engine = engine,
                               table = table,
                               fk_symbol = cur_key.name)


    # I couldn't figure out how to get the existing unique constraints.
    # Therefore, remove all existing unique constraints and than add the new
    # ones.
    #const_to_remove = exist_table.constraints.difference(new_table.constraints)
    #for cur_const in const_to_remove:
    #    if isinstance(cur_const, sqa.schema.PrimaryKeyConstraint):
    #        logger.error("Changing a primary key is not supported. (%s)", cur_const)
    #        continue
    #    table_updated = True
    insp = sqa.inspect(engine)
    unique_const = insp.get_unique_constraints(exist_table.name)
    for cur_const in unique_const:
        remove_unique_constraint(engine, table, cur_const['name'])


    const_to_add = new_table.constraints.difference(exist_table.constraints)
    for cur_const in const_to_add:
        if isinstance(cur_const, sqa.schema.PrimaryKeyConstraint):
            logger.error("Changing a primary key is not supported. (%s)", cur_const)
            continue
        add_unique_constraint(engine, table, cur_const)
        table_updated = True

    return table_updated


def add_column(engine, table, column, prefix):
    ''' Add a column to a database table.
    '''
    table_name = table.__table__.name
    column_type = column.type.compile(engine.dialect)
    if column.nullable:
        engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column.name, column_type))
    else:
        engine.execute('ALTER TABLE %s ADD COLUMN %s %s NOT NULL' % (table_name, column.name, column_type))

    for cur_key in column.foreign_keys:
        add_foreign_key(engine = engine,
                        table = table,
                        column = column,
                        target = prefix + cur_key.target_fullname)

def remove_column(engine, table, column):
    ''' Remove a column from the database table.
    '''
    table_name = table.__table__.name
    for cur_key in column.foreign_keys:
        remove_foreign_key(engine, table, cur_key.name)
    engine.execute('ALTER TABLE %s DROP COLUMN %s' % (table_name, column.name))


def change_column_type(engine, table, column):
    ''' Change the type of a database table column.
    '''
    table_name = table.__table__.name
    column_type = column.type.compile(dialect = engine.dialect)
    engine.execute('ALTER TABLE %s MODIFY %s %s' % (table_name, column.name, column_type))


def add_foreign_key(engine, table, column, target):
    ''' Add a foreign key to the column.
    '''
    table_name = table.__table__.name
    tmp = target.split('.')
    target_table = tmp[0]
    target_column = tmp[1]
    engine.execute('ALTER TABLE %s ADD FOREIGN KEY (%s) REFERENCES %s(%s)' % (table_name, column.name, target_table, target_column))


def remove_foreign_key(engine, table, fk_symbol):
    ''' Remove a foreign key.
    '''
    table_name = table.__table__.name
    engine.execute('ALTER TABLE %s DROP FOREIGN KEY %s' % (table_name, fk_symbol))


def add_unique_constraint(engine, table, constraint):
    ''' Add a unique constraint to the table.
    '''
    table_name = table.__table__.name
    col_names = [x.name for x in constraint.columns]
    const_name = constraint.name

    if const_name:
        sql_cmd = 'ALTER TABLE %s ADD CONSTRAINT %s UNIQUE (%s)' % (table_name, const_name, ','.join(col_names))
    else:
        sql_cmd = 'ALTER TABLE %s ADD CONSTRAINT UNIQUE (%s)' % (table_name, ','.join(col_names))

    engine.execute(sql_cmd)


def remove_unique_constraint(engine, table, name):
    ''' Remove a unique constraint from the table using the constraint name.
    '''
    table_name = table.__table__.name
    engine.execute('ALTER TABLE %s DROP INDEX %s' % (table_name, name))


def compare_column_type(col1, col2):
    ''' Compare the type of two columns.
    '''
    is_equal = False
    tmp = re.split('[()]', col1)
    if tmp:
        if len(tmp) >= 1:
            col1_type = tmp[0]

        if len(tmp) >= 2:
            col1_len = tmp[1]
        else:
            col1_len = None

    tmp = re.split('[()]', col2)
    if tmp:
        if len(tmp) >= 1:
            col2_type = tmp[0]

        if len(tmp) >= 2:
            col2_len = tmp[1]
        else:
            col2_len = None

    if col1_type == col2_type:
        if col1_len is not None:
            if col1_len == col2_len:
                is_equal = True
        else:
            is_equal = True

    return is_equal


