// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
