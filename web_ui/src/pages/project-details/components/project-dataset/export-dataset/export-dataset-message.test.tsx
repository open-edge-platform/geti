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

import { render, RenderResult, screen } from '@testing-library/react';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ExportFormats } from '../../../../../core/projects/dataset.interface';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { ExportDatasetMessage } from './export-dataset-message.component';
import {
    CLASSIFICATION_MESSAGE,
    EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE,
    ROTATED_BOUNDING_MESSAGE,
    TASK_CHAIN_MESSAGE,
} from './utils';

describe('ExportDatasetMessage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const App = ({
        project,
        exportFormat,
        hasVideos = true,
        isTaskChainProject,
    }: {
        project: ProjectProps;
        exportFormat: ExportFormats;
        isTaskChainProject: boolean;
        hasVideos?: boolean;
    }) => {
        return (
            <ExportDatasetMessage
                project={project}
                hasVideos={hasVideos}
                exportFormat={exportFormat}
                isTaskChainProject={isTaskChainProject}
            />
        );
    };

    const renderApp = async ({
        project,
        exportFormat,
        hasVideos = true,
        isTaskChainProject = false,
    }: {
        project: ProjectProps;
        exportFormat: ExportFormats;
        isTaskChainProject?: boolean;
        hasVideos?: boolean;
    }): Promise<RenderResult> => {
        return render(
            <App
                project={project}
                exportFormat={exportFormat}
                isTaskChainProject={isTaskChainProject}
                hasVideos={hasVideos}
            />
        );
    };

    const getMockedProject = (domains: DOMAIN[]): ProjectProps =>
        ({
            domains,
        }) as ProjectProps;

    it('Renders empty when there is no message to show', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.CLASSIFICATION]),
            hasVideos: false,
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.queryByText('Converted formats')).not.toBeInTheDocument();
    });

    it('classification & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.CLASSIFICATION]),
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it('classification & "voc" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.CLASSIFICATION]),
            exportFormat: ExportFormats.VOC,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).toBeVisible();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it('detection rotated bounding box & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.DETECTION_ROTATED_BOUNDING_BOX]),
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it.each([ExportFormats.VOC, ExportFormats.COCO, ExportFormats.YOLO])(
        'detection rotated bounding box & "%s" format',
        async (format) => {
            await renderApp({
                project: getMockedProject([DOMAIN.DETECTION_ROTATED_BOUNDING_BOX]),
                exportFormat: format,
            });

            expect(screen.getByText('Converted formats')).toBeVisible();

            expect(screen.getByText(ROTATED_BOUNDING_MESSAGE)).toBeVisible();
            expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

            expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
        }
    );

    it('anomaly detection & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.ANOMALY_DETECTION]),
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it('anomaly classification & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.ANOMALY_CLASSIFICATION]),
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it('anomaly segmentation & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.ANOMALY_SEGMENTATION]),
            exportFormat: ExportFormats.DATUMARO,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it('task chain & "datumaro" format', async () => {
        await renderApp({
            project: getMockedProject([DOMAIN.SEGMENTATION]),
            exportFormat: ExportFormats.DATUMARO,
            isTaskChainProject: true,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it.each([ExportFormats.VOC, ExportFormats.COCO])('task chain & "%s" format', async (format) => {
        await renderApp({
            project: getMockedProject([DOMAIN.SEGMENTATION]),
            exportFormat: format,
            isTaskChainProject: true,
        });

        expect(screen.getByText('Converted formats')).toBeVisible();

        expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
        expect(screen.getByText(TASK_CHAIN_MESSAGE)).toBeVisible();
        expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

        expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
    });

    it.each([ExportFormats.DATUMARO, ExportFormats.VOC, ExportFormats.COCO, ExportFormats.YOLO])(
        'segmentation semantic & "%s" format',
        async (format) => {
            await renderApp({
                project: getMockedProject([DOMAIN.SEGMENTATION]),
                exportFormat: format,
            });

            expect(screen.getByText('Converted formats')).toBeVisible();

            expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

            expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
        }
    );

    it.each([ExportFormats.DATUMARO, ExportFormats.VOC, ExportFormats.COCO, ExportFormats.YOLO])(
        'segmentation instance & "%s" format',
        async (format) => {
            await renderApp({
                project: getMockedProject([DOMAIN.SEGMENTATION_INSTANCE]),
                exportFormat: format,
            });

            expect(screen.getByText('Converted formats')).toBeVisible();

            expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

            expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
        }
    );

    it.each([ExportFormats.DATUMARO, ExportFormats.VOC, ExportFormats.COCO, ExportFormats.YOLO])(
        'detection & "%s" format',
        async (format) => {
            await renderApp({
                project: getMockedProject([DOMAIN.DETECTION]),
                exportFormat: format,
            });

            expect(screen.getByText('Converted formats')).toBeVisible();

            expect(screen.queryByText(ROTATED_BOUNDING_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(TASK_CHAIN_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(CLASSIFICATION_MESSAGE)).not.toBeInTheDocument();

            expect(screen.getByText(EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE)).toBeVisible();
        }
    );
});
