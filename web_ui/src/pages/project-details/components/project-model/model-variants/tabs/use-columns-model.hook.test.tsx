// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Column, Row, TableBody, TableHeader, TableView } from '@adobe/react-spectrum';
import { fireEvent, renderHook, screen, waitFor } from '@testing-library/react';

import { createInMemoryApiModelConfigParametersService } from '../../../../../../core/configurable-parameters/services/in-memory-api-model-config-parameters-service';
import { OptimizedModel, TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { mockedOptimizedModels, mockedTrainedModel } from '../../../../../../core/models/services/test-utils';
import { downloadFile } from '../../../../../../shared/utils';
import { providersRender, RequiredProviders } from '../../../../../../test-utils/required-providers-render';
import { ModelTableColumns } from '../model-table/model-table.interface';
import { useColumnsModel } from './use-columns-model.hook';

jest.mock('../../../../../../shared/utils', () => ({
    ...jest.requireActual('../../../../../../shared/utils'),
    downloadFile: jest.fn(),
}));

const mockedModelIdentifier = {
    modelId: 'modelId-test',
    groupId: 'groupId-test',
    projectId: 'projectId-test',
    workspaceId: 'workspaceId-test',
    organizationId: 'organizationId-test',
};
jest.mock('../../../../../../hooks/use-model-identifier/use-model-identifier.hook', () => ({
    ...jest.requireActual('../../../../../../hooks/use-model-identifier/use-model-identifier.hook'),
    useModelIdentifier: jest.fn(() => mockedModelIdentifier),
}));

const loadedOptimizedModel: OptimizedModel = mockedOptimizedModels[0];
const pendingOptimizedModel: OptimizedModel = { ...mockedOptimizedModels[0], precision: [], modelStatus: 'NOT_READY' };

describe('useColumnsModel', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const renderUseColumnsModel = (
        { hideMenu, setSelectedModel } = { hideMenu: false, setSelectedModel: jest.fn() }
    ) => {
        return renderHook(
            () =>
                useColumnsModel({
                    taskId: '123',
                    hideMenu,
                    version: 1,
                    groupName: 'groupName-test',
                    setSelectedModel,
                    modelTemplateName: 'modelTemplateName',
                }),
            {
                wrapper: ({ children }: { children: ReactNode }) => (
                    <RequiredProviders configParametersService={createInMemoryApiModelConfigParametersService()}>
                        {children}
                    </RequiredProviders>
                ),
            }
        );
    };
    const renderColumn = (
        column: ModelTableColumns<OptimizedModel | TrainedModel>,
        model: OptimizedModel | TrainedModel
    ) =>
        providersRender(
            <TableView>
                <TableHeader columns={[column]}>
                    <Column key={column.label}>{column.label}</Column>
                </TableHeader>
                <TableBody>
                    <Row>{column.component(model)}</Row>
                </TableBody>
            </TableView>
        );

    const columnHeaderName = 'OPTIMIZED MODELS';
    const defaultDescription = 'description-test';
    const { result } = renderUseColumnsModel();
    const [headColum, licenseColumn, precisionColumn, accuracyColumn, sizeColumn, menuColumn] = result.current(
        columnHeaderName,
        defaultDescription
    );

    describe('columnHeader', () => {
        it('custom column header name and description', async () => {
            renderColumn(headColum, loadedOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: columnHeaderName })).toBeVisible();
                expect(
                    screen.getByRole('rowheader', { name: `${loadedOptimizedModel.modelName} ${defaultDescription}` })
                ).toBeVisible();
            });
        });
    });

    describe('license', () => {
        it('render model license', async () => {
            renderColumn(licenseColumn, loadedOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'LICENSE' })).toBeVisible();
                expect(screen.getByRole('rowheader', { name: loadedOptimizedModel.license })).toBeVisible();
            });
        });
    });

    describe('precision', () => {
        it('flashing animation', async () => {
            renderColumn(precisionColumn, pendingOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'PRECISION' })).toBeVisible();
                expect(screen.getByLabelText('three dots flashing animation')).toBeVisible();
            });
        });

        it('render model precision', async () => {
            renderColumn(precisionColumn, loadedOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'PRECISION' })).toBeVisible();
                expect(screen.getByRole('rowheader', { name: loadedOptimizedModel.precision[0] })).toBeVisible();
            });
        });
    });

    describe('accuracy', () => {
        it('renders empty row when accuracy is falsy', async () => {
            renderColumn(accuracyColumn, { ...loadedOptimizedModel, accuracy: null });

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'SCORE' })).toBeVisible();
                expect(screen.getByRole('rowheader')).toHaveTextContent('');
            });
        });

        it('flashing animation', async () => {
            renderColumn(accuracyColumn, pendingOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'SCORE' })).toBeVisible();
                expect(screen.getByLabelText('three dots flashing animation')).toBeVisible();
            });
        });

        it('accuracy gets formatted to percentage', async () => {
            renderColumn(accuracyColumn, loadedOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'SCORE' })).toBeVisible();
                expect(screen.getByRole('rowheader')).toHaveTextContent('48.4%');
            });
        });
    });

    describe('size', () => {
        it('render model size column', async () => {
            renderColumn(sizeColumn, loadedOptimizedModel);

            await waitFor(() => {
                expect(screen.getByRole('columnheader', { name: 'SIZE' })).toBeVisible();
                expect(screen.getByRole('rowheader', { name: loadedOptimizedModel.modelSize })).toBeVisible();
            });
        });
    });

    describe('menu', () => {
        describe('empty column', () => {
            it('model is pending', async () => {
                renderColumn(menuColumn, pendingOptimizedModel);

                await waitFor(() => {
                    expect(screen.getByRole('rowheader')).toHaveTextContent('');
                });
            });

            it('"hideMenu" is set to true', async () => {
                const response = renderUseColumnsModel({ hideMenu: true, setSelectedModel: jest.fn() });

                const hiddenMenuColumn = response.result.current('OPTIMIZED MODELS', 'description-test').at(-1);

                hiddenMenuColumn && renderColumn(hiddenMenuColumn, loadedOptimizedModel);

                await waitFor(() => {
                    expect(screen.getByRole('rowheader')).toHaveTextContent('');
                });
            });
        });

        describe('download url', () => {
            it('EXPORT_OPTIMIZED_MODEL', async () => {
                renderColumn(menuColumn, loadedOptimizedModel);

                fireEvent.click(screen.getByRole('button', { name: /download model/i }));

                expect(downloadFile).toHaveBeenCalledWith(
                    expect.stringContaining(
                        `${mockedModelIdentifier.modelId}/optimized_models/${loadedOptimizedModel.id}/export?model_only=true`
                    )
                );
            });

            it('EXPORT_MODEL', async () => {
                renderColumn(menuColumn, mockedTrainedModel);

                fireEvent.click(screen.getByRole('button', { name: /download model/i }));

                expect(downloadFile).toHaveBeenCalledWith(
                    expect.stringContaining(`${mockedModelIdentifier.modelId}/export?model_only=true`)
                );
            });
        });
    });
});
