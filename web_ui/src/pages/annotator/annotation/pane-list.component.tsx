// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import React, { ReactNode } from 'react';

import { Allotment } from 'allotment';

import 'allotment/dist/style.css';

interface PaneListProps {
    itemsList: ReactNode;
    listActions: ReactNode;
    thumbnailGrid?: ReactNode;
}

export const PaneList = ({ itemsList, listActions, thumbnailGrid = null }: PaneListProps) => {
    return (
        <Allotment vertical>
            {thumbnailGrid}

            <Allotment.Pane>
                <div style={{ height: 'calc(100% - var(--spectrum-global-dimension-size-675))' }}>
                    {listActions}
                    {itemsList}
                </div>
            </Allotment.Pane>
        </Allotment>
    );
};
