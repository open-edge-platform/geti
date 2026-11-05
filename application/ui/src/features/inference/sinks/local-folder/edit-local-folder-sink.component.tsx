// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';

import { EditSink } from '../deprecated/edit-sink/edit-sink.component';
import { LocalFolder } from '../deprecated/local-folder/local-folder.component';
import { localFolderBodyFormatter } from '../deprecated/local-folder/utils';
import type { EditSinkProps } from '../types';

export const EditLocalFolderSink = ({
    sink,
    isConnected,
    onSaved,
    onBackToList,
}: EditSinkProps<LocalFolderSinkConfig>) => (
    <EditSink
        config={sink}
        isConnected={isConnected}
        onSaved={onSaved}
        onBackToList={onBackToList}
        componentFields={(state) => <LocalFolder defaultState={state} />}
        bodyFormatter={localFolderBodyFormatter}
    />
);
