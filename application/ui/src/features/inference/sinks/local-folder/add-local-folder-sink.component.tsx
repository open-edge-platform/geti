// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AddSink } from '../deprecated/add-sink/add-sink.component';
import { LocalFolder } from '../deprecated/local-folder/local-folder.component';
import { getLocalFolderInitialConfig, localFolderBodyFormatter } from '../deprecated/local-folder/utils';
import type { AddSinkProps } from '../types';

export const AddLocalFolderSink = ({ onSaved }: AddSinkProps) => (
    <AddSink
        onSaved={onSaved}
        config={getLocalFolderInitialConfig()}
        componentFields={(state) => <LocalFolder defaultState={state} />}
        bodyFormatter={localFolderBodyFormatter}
    />
);
