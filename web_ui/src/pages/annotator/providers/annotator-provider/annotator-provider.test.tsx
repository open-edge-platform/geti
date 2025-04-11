// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactElement } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { createInMemoryAnnotationService } from '../../../../core/annotations/services/in-memory-annotation-service';
import { createInMemoryInferenceService } from '../../../../core/annotations/services/in-memory-inference-service';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import { useAnnotationScene } from '../annotation-scene-provider/annotation-scene-provider.component';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';

const mockedLabel = labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }));
const mockedAnnotation = getMockedAnnotation({ labels: [mockedLabel] }, ShapeType.Rect);
const mockedInvalidAnnotation = getMockedAnnotation({ id: 'invalid-annotation', labels: [] }, ShapeType.Rect);
const mockedPrediction = getMockedAnnotation({ id: 'prediction', labels: [mockedLabel] }, ShapeType.Rect);

describe('Annotator provider', (): void => {
    const annotationService = createInMemoryAnnotationService();
    const inferenceService = createInMemoryInferenceService();
    const mediaService = createInMemoryMediaService();
    const projectService = createInMemoryProjectService();

    const projectIdentifier = {
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
        projectId: 'project-id',
    };

    const render = (ui: ReactElement) => {
        return annotatorRender(ui, {
            projectIdentifier,
            services: { annotationService, mediaService, inferenceService, projectService },
        });
    };

    it('Loads project details then shows the app', async () => {
        const App = () => {
            const { project } = useProject();

            return <span>{project.name}</span>;
        };

        await render(<App />);

        expect(await screen.findByText('In memory segmentation')).toBeInTheDocument();
    });

    describe('userScene annotations', () => {
        // Immediately load the media item's image
        let imageLoadTimeout: NodeJS.Timeout | null = null;

        beforeAll(() => {
            Object.defineProperty(global.Image.prototype, 'onload', {
                value: () => null,
                writable: true,
                configurable: true,
            });

            // Immediately load the media item's image
            Object.defineProperty(global.Image.prototype, 'src', {
                set() {
                    imageLoadTimeout = setTimeout(() => this.onload());
                },
            });
        });

        afterAll(() => {
            if (imageLoadTimeout) {
                clearTimeout(imageLoadTimeout);
            }
        });

        const mediaItem: MediaItem = getMockedImageMediaItem({
            identifier: {
                imageId: 'test',
                type: MEDIA_TYPE.IMAGE,
            },
        });

        const App = () => {
            const scene = useAnnotationScene();
            const { selectedMediaItem, setSelectedMediaItem } = useSelectedMediaItem();

            const loadMediaItem = () => setSelectedMediaItem(mediaItem);

            if (selectedMediaItem === undefined) {
                return <button onClick={loadMediaItem}>Load</button>;
            }

            return (
                <div>
                    <ul aria-label='annotations'>
                        {scene.annotations?.map((annotation) => <li key={annotation.id}>{annotation.id}</li>)}
                    </ul>
                </div>
            );
        };

        it('valid annotations', async () => {
            const annotationsSpy = jest.spyOn(annotationService, 'getAnnotations').mockImplementation(async () => {
                return [mockedAnnotation];
            });
            const predictionsSpy = jest.spyOn(inferenceService, 'getPredictions').mockImplementation(async () => {
                return [mockedPrediction];
            });

            await render(<App />);

            fireEvent.click(await screen.findByRole('button', { name: /load/i }));
            await waitFor(() => expect(screen.getAllByRole('listitem')).toHaveLength(1));

            expect(screen.queryByText(mockedAnnotation.id)).toBeInTheDocument();

            annotationsSpy.mockRestore();
            predictionsSpy.mockRestore();
        });

        it('invalid annotations', async () => {
            const annotationsSpy = jest.spyOn(annotationService, 'getAnnotations').mockImplementation(async () => {
                return [mockedInvalidAnnotation];
            });

            const predictionsSpy = jest.spyOn(inferenceService, 'getPredictions').mockImplementation(async () => {
                return [mockedPrediction];
            });

            await render(<App />);

            fireEvent.click(await screen.findByRole('button', { name: /load/i }));
            await waitFor(() => expect(screen.getAllByRole('listitem')).toHaveLength(1));

            expect(screen.queryByText(mockedPrediction.id)).toBeInTheDocument();

            annotationsSpy.mockRestore();
            predictionsSpy.mockRestore();
        });

        it('empty annotations', async () => {
            const annotationsSpy = jest.spyOn(annotationService, 'getAnnotations').mockImplementation(async () => {
                return [];
            });

            const predictionsSpy = jest.spyOn(inferenceService, 'getPredictions').mockImplementation(async () => {
                return [mockedPrediction];
            });

            await render(<App />);

            fireEvent.click(await screen.findByRole('button', { name: /load/i }));
            await waitFor(() => expect(screen.getAllByRole('listitem')).toHaveLength(1));

            expect(screen.queryByText(mockedPrediction.id)).toBeInTheDocument();

            annotationsSpy.mockRestore();
            predictionsSpy.mockRestore();
        });
    });
});
