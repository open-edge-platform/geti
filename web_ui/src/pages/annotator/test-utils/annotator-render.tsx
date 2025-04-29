// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement, ReactNode } from 'react';

import { RenderOptions, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { CustomFeatureFlags } from '../../../core/feature-flags/services/feature-flag-service.interface';
import { ProjectIdentifier } from '../../../core/projects/core.interface';
import { DatasetIdentifier } from '../../../core/projects/dataset.interface';
import { ApplicationServicesContextProps } from '../../../core/services/application-services-provider.component';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender } from '../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { AnnotatorProvider } from '../providers/annotator-provider/annotator-provider.component';
import { DatasetProvider } from '../providers/dataset-provider/dataset-provider.component';
import { RegionOfInterestProvider } from '../providers/region-of-interest-provider/region-of-interest-provider.component';
import { SelectedMediaItemProvider } from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from '../providers/task-provider/task-provider.component';

interface AnnotatorProvidersProps {
    children?: ReactNode;
    datasetIdentifier: DatasetIdentifier;
}

export const AnnotatorProviders = ({ children, datasetIdentifier }: AnnotatorProvidersProps): JSX.Element => {
    return (
        <ProjectProvider
            projectIdentifier={{
                organizationId: datasetIdentifier.organizationId,
                projectId: datasetIdentifier.projectId,
                workspaceId: datasetIdentifier.workspaceId,
            }}
        >
            <TaskProvider>
                <DatasetProvider>
                    <SelectedMediaItemProvider>
                        <AnnotatorProvider>
                            <RegionOfInterestProvider>{children} </RegionOfInterestProvider>
                        </AnnotatorProvider>
                    </SelectedMediaItemProvider>
                </DatasetProvider>
            </TaskProvider>
        </ProjectProvider>
    );
};

interface CustomRenderOptions extends Omit<RenderOptions, 'queries'> {
    projectIdentifier?: ProjectIdentifier;
    datasetIdentifier?: DatasetIdentifier;
    services?: Partial<ApplicationServicesContextProps>;
    featureFlags?: CustomFeatureFlags;
    initialEntries?: string[];
}

const customRender = async (
    ui: ReactElement,
    options: CustomRenderOptions = {
        projectIdentifier: getMockedProjectIdentifier({ workspaceId: 'test-workspace', projectId: '1' }),
    }
) => {
    const projectIdentifier =
        options.projectIdentifier ??
        getMockedProjectIdentifier({
            projectId: '1',
            workspaceId: 'test-workspace',
            organizationId: '000000000000000000000001',
        });

    const datasetIdentifier = options.datasetIdentifier ?? { ...projectIdentifier, datasetId: 'test' };

    const wrappedByAnnotatorProviders = (
        <AnnotatorProviders datasetIdentifier={datasetIdentifier}>{ui}</AnnotatorProviders>
    );

    const result = providersRender(wrappedByAnnotatorProviders, options);

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return result;
};

// override render method
export { customRender as annotatorRender };
