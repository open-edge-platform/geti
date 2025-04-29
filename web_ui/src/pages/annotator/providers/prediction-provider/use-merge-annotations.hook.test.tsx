// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../core/projects/services/project-service.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { SelectedMediaItemProvider } from '../selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from '../task-provider/task-provider.component';
import { useMergeAnnotations } from './use-merge-annotations.hook';

const mockRoi = { x: 0, y: 0, width: 600, height: 400, shapeType: ShapeType.Rect };
jest.mock('../../hooks/use-image-roi.hook', () => ({
    useImageROI: jest.fn(() => mockRoi),
}));

const wrapper = ({ children }: { children?: ReactNode }) => (
    <ProjectProvider
        projectIdentifier={{
            workspaceId: 'workspace-id',
            projectId: 'project-id',
            organizationId: 'organization-id',
        }}
    >
        <TaskProvider>
            <SelectedMediaItemProvider>{children}</SelectedMediaItemProvider>
        </TaskProvider>
    </ProjectProvider>
);

const mockLabel = (label: Partial<Label>, score = 1) =>
    ({
        ...getMockedLabel(label),
        score,
    }) as AnnotationLabel;
const mockedNoObjectAnnotation = getMockedAnnotation({
    shape: { ...mockRoi, shapeType: ShapeType.Rect },
    labels: [
        mockLabel({ id: '321', name: 'No object', behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL }, 0),
    ],
});

const mockedGlobalAnomalous = getMockedAnnotation({
    labels: [
        labelFromUser(
            getMockedLabel({
                id: 'anomalous-label-id',
                name: 'Anomalous',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
            })
        ),
    ],
    shape: { ...mockRoi, shapeType: ShapeType.Rect },
});
const mockedNormal = getMockedAnnotation({
    labels: [
        labelFromUser(
            getMockedLabel({
                id: 'normal',
                name: 'Normal',
                behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.EXCLUSIVE,
            })
        ),
    ],
    shape: { ...mockRoi, shapeType: ShapeType.Rect },
});

const mockedLocalAnomalous = getMockedAnnotation(
    {
        labels: [
            labelFromUser(
                getMockedLabel({
                    id: 'local-anomalous-label-id',
                    name: 'Anomalous',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
                })
            ),
        ],
    },
    ShapeType.Polygon
);

const renderMergeAnnotationsHook = (params: { projectService: ProjectService }) => {
    return renderHookWithProviders(useMergeAnnotations, {
        wrapper: ({ children }) => wrapper({ children }),
        providerProps: { projectService: params.projectService },
    });
};

describe('useMergeAnnotations', () => {
    it('replace old global annotations', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const mockAnnotation = { ...mockedNoObjectAnnotation, id: '123' };
        const mockAnnotationPrediction = { ...mockedNoObjectAnnotation, id: '321' };

        await waitFor(() => {
            expect(result.current([mockAnnotationPrediction], [mockAnnotation])).toEqual([mockAnnotationPrediction]);
        });
    });

    it('merge duplicate annotations', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const mockAnnotation = getMockedAnnotation({ id: 'annotation-1', labels: [mockLabel({ id: '123' }, 0.01)] });
        const mockPrediction = getMockedAnnotation({ id: 'prediction-1', labels: [mockLabel({ id: '123' }, 0.01)] });

        await waitFor(() => {
            expect(result.current([mockPrediction], [mockAnnotation, mockPrediction])).toEqual([
                mockAnnotation,
                mockPrediction,
            ]);
        });
    });

    it('replace annotations with "NoObject" prediction', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const mockAnnotation = getMockedAnnotation({ id: 'test-1', labels: [mockLabel({ id: '123' }, 0.01)] });
        const NoObjectPrediction = { ...mockedNoObjectAnnotation, id: '321' };

        await waitFor(() => {
            expect(result.current([NoObjectPrediction], [mockAnnotation, mockAnnotation])).toEqual([
                NoObjectPrediction,
            ]);
        });
    });

    it('replace "NoObject" annotation with prediction', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const noObjectAnnotation = { ...mockedNoObjectAnnotation, id: '321' };
        const prediction = getMockedAnnotation({ id: 'test-1', labels: [mockLabel({ id: '123' }, 0.01)] });

        await waitFor(() => {
            expect(result.current([prediction], [noObjectAnnotation])).toEqual([prediction]);
        });
    });

    it('replace "normal" with global and local anomalous', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const annotations = [{ ...mockedNormal }];
        const predictions = [{ ...mockedGlobalAnomalous }, { ...mockedLocalAnomalous }];

        await waitFor(() => {
            expect(result.current(predictions, annotations)).toEqual(predictions);
        });
    });

    it('replace global anomalous with "normal" ', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const predictions = [{ ...mockedNormal }];
        const annotations = [{ ...mockedGlobalAnomalous }];

        await waitFor(() => {
            expect(result.current(predictions, annotations)).toEqual(predictions);
        });
    });

    it('merge global anomalous with global anomalous', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const annotations = [{ ...mockedGlobalAnomalous, id: '1111' }, { ...mockedLocalAnomalous }];
        const predictions = [{ ...mockedGlobalAnomalous, id: '2211' }, { ...mockedLocalAnomalous }];

        await waitFor(() => {
            expect(result.current(predictions, annotations)).toEqual(predictions);
        });
    });

    it('replace "normal" annotations', async () => {
        const projectService = createInMemoryProjectService();
        const { result } = renderMergeAnnotationsHook({ projectService });

        const annotations = [{ ...mockedNormal, id: '123' }];
        const predictions = [{ ...mockedNormal, id: '321' }];

        await waitFor(() => {
            expect(result.current(predictions, annotations)).toEqual(predictions);
        });
    });
});
