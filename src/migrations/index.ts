import * as migration_20261118_002235_initial from './20261118_002235_initial';
import * as migration_20261118_010817_blob_object_key from './20261118_010817_blob_object_key';

export const migrations = [
  {
    up: migration_20261118_002235_initial.up,
    down: migration_20261118_002235_initial.down,
    name: '20261118_002235_initial',
  },
  {
    up: migration_20261118_010817_blob_object_key.up,
    down: migration_20261118_010817_blob_object_key.down,
    name: '20261118_010817_blob_object_key'
  },
];
