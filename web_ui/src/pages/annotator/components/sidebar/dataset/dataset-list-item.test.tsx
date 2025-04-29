// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { getMockedImageMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { DatasetItemMenu } from './dataset-item-menu.component';
import { DatasetListItem } from './dataset-list-item.component';

describe('DatasetListItem', () => {
    const mediaItem = getMockedImageMediaItem({
        annotationStatePerTask: [{ taskId: 'task-id', state: MEDIA_ANNOTATION_STATUS.ANNOTATED }],
    });
    const isSelected = true;

    const renderApp = async (shouldShowAnnotationIndicator = true) => {
        await render(
            <DatasetListItem
                mediaItem={mediaItem}
                isSelected={isSelected}
                selectMediaItem={jest.fn()}
                shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                datasetItemMenu={<DatasetItemMenu mediaItem={mediaItem} isSelected={isSelected} />}
            />
        );
    };

    it('should have menu with delete option', async () => {
        await renderApp();

        await waitFor(() => {
            fireEvent.load(screen.getByAltText(mediaItem.name));
        });

        fireEvent.click(await screen.findByRole('button', { name: 'open menu' }));
        expect(screen.getByText('Delete')).toBeInTheDocument();
    });
});
