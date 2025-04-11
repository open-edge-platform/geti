// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { getMockedImageMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { projectRender } from '../../../../../test-utils/project-provider-render';
import { DatasetProvider } from '../../../providers/dataset-provider/dataset-provider.component';
import { SelectedMediaItemProvider } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { DatasetItemMenu } from './dataset-item-menu.component';

describe('Annotator dataset menu items', () => {
    it('Check menu items - Delete and Download', async () => {
        await projectRender(
            <TaskProvider>
                <DatasetProvider>
                    <SelectedMediaItemProvider>
                        <DatasetItemMenu
                            mediaItem={getMockedImageMediaItem({ name: 'test image' })}
                            isSelected={false}
                        />
                    </SelectedMediaItemProvider>
                </DatasetProvider>
            </TaskProvider>
        );

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems).toHaveLength(2);
        expect(menuItems[0]).toHaveTextContent('Delete');
        expect(menuItems[1]).toHaveTextContent('Download');
    });
});
