// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../../../../core/projects/core.interface';
import { getMockedSupportedAlgorithm } from '../../../../../../../core/supported-algorithms/services/test-utils';
import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { getMockedProjectIdentifier } from '../../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../../providers/project-provider/project-provider.component';
import { ModelTemplatesList } from './model-templates-list.component';

const getTemplateId = ({ name }: SupportedAlgorithm) => `${name.toLowerCase()}-id`;
const getCardsIds = () => screen.getAllByLabelText(/selected/i).map(({ id }) => id);

describe('ModelTemplatesSelection', () => {
    const recommendedTemplate = getMockedSupportedAlgorithm({
        name: 'SSD',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_ssd',
        gigaflops: 5.4,
        summary: 'SSD architecture for detection',
        isDefaultAlgorithm: true,
    });

    const otherRecommendedTemplate = getMockedSupportedAlgorithm({
        name: 'SSD-2',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_ssd_2',
        gigaflops: 5.4,
        summary: 'SSD-2 architecture for detection',
        isDefaultAlgorithm: true,
    });
    const smallSizeTemplate = getMockedSupportedAlgorithm({
        name: 'ATTS',
        domain: DOMAIN.DETECTION,
        modelSize: 5,
        modelTemplateId: 'detection_atts',
        gigaflops: 3,
        isDefaultAlgorithm: true,
        summary: 'ATTS architecture for detection',
    });
    const bigSizeTemplate = getMockedSupportedAlgorithm({
        name: 'YOLO',
        domain: DOMAIN.DETECTION,
        modelSize: 200,
        modelTemplateId: 'detection_yolo',
        gigaflops: 2.3,
        summary: 'YOLO architecture for detection',
    });

    const lowComplexityTemplate = getMockedSupportedAlgorithm({
        name: 'TINY',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_tiny',
        gigaflops: 0.3,
        summary: 'TINY architecture for detection',
    });

    const highComplexityTemplate = getMockedSupportedAlgorithm({
        name: 'TINY-2',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_tiny_2',
        gigaflops: 100.3,
        summary: 'TINY-2 architecture for detection',
    });

    const mockedSupportedAlgorithmsForDetection = [
        highComplexityTemplate,
        lowComplexityTemplate,
        bigSizeTemplate,
        recommendedTemplate,
        smallSizeTemplate,
        otherRecommendedTemplate,
    ];

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const renderApp = async () => {
        render(
            <ProjectProvider
                projectIdentifier={getMockedProjectIdentifier({
                    workspaceId: 'workspace-id',
                    projectId: 'single-project-id',
                })}
            >
                <ModelTemplatesList
                    templates={mockedSupportedAlgorithmsForDetection}
                    selectedDomain={DOMAIN.DETECTION}
                    animationDirection={1}
                    selectedModelTemplateId={''}
                    handleSelectedTemplateId={jest.fn()}
                    activeModelTemplateIdPerTask={mockedSupportedAlgorithmsForDetection[0].modelTemplateId}
                />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('Templates are sorted by relevance by default', async () => {
        await renderApp();

        const [firstElement, secondElement] = getCardsIds();

        expect(firstElement).toEqual(getTemplateId(recommendedTemplate));
        expect(secondElement).toEqual(getTemplateId(smallSizeTemplate));
    });

    it('sorted by size desc', async () => {
        await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /sort by/i }));
        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: 'Size: Small to big' })
        );

        const [firstElement] = getCardsIds();
        expect(firstElement).toEqual(getTemplateId(smallSizeTemplate));
    });

    it('sorted by size asc', async () => {
        await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /sort by/i }));
        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: 'Size: Big to small' })
        );

        const [firstElement] = getCardsIds();
        expect(firstElement).toEqual(getTemplateId(bigSizeTemplate));
    });

    it('sorted by complexity asc', async () => {
        await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /sort by/i }));
        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: 'Complexity: Low to high' })
        );

        const [firstElement] = getCardsIds();
        expect(firstElement).toEqual(getTemplateId(lowComplexityTemplate));
    });

    it('sorted by complexity desc', async () => {
        await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /sort by/i }));
        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: 'Complexity: High to low' })
        );

        const [firstElement] = getCardsIds();
        expect(firstElement).toEqual(getTemplateId(highComplexityTemplate));
    });
});
