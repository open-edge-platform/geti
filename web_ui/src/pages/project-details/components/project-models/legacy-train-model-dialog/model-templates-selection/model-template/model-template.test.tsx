// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ThemeProvider } from '@geti/ui/theme';
import { fireEvent, render, screen, within } from '@testing-library/react';

import {
    LifecycleStage,
    PerformanceCategory,
} from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { getMockedSupportedAlgorithm } from '../../../../../../../core/supported-algorithms/services/test-utils';
import { idMatchingFormat } from '../../../../../../../test-utils/id-utils';
import { checkTooltip } from '../../../../../../../test-utils/utils';
import { ModelTemplate } from './model-template.component';

describe('ModelTemplate', () => {
    const activeModelTemplateIdPerTask = 'atts-id';

    const defaultTemplate = getMockedSupportedAlgorithm({
        summary: 'Cool template',
        name: 'ATSS',
        gigaflops: 4.3,
        modelSize: 2,
        modelTemplateId: activeModelTemplateIdPerTask,
    });

    const handleSelectedTemplateId = jest.fn();

    const renderApp = ({
        template = defaultTemplate,
        selectedModelTemplateId = defaultTemplate.modelTemplateId,
        activeModelId = activeModelTemplateIdPerTask,
    }) => {
        return render(
            <ThemeProvider>
                <ModelTemplate
                    template={template}
                    selectedModelTemplateId={selectedModelTemplateId}
                    handleSelectedTemplateId={handleSelectedTemplateId}
                    activeModelTemplateIdPerTask={activeModelId}
                />
            </ThemeProvider>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('should have radio button and be ticked when is selected', () => {
        renderApp({});

        expect(screen.getByRole('radio', { name: defaultTemplate.name })).toBeChecked();
    });

    it('should have radio button and not be ticked when is not selected', () => {
        renderApp({ selectedModelTemplateId: 'yolo-id' });

        expect(screen.getByRole('radio', { name: defaultTemplate.name })).not.toBeChecked();
    });

    it('should show proper tooltip for the algorithm name', async () => {
        jest.useFakeTimers();

        renderApp({});

        await checkTooltip(screen.getByLabelText(defaultTemplate.name), defaultTemplate.name);
    });

    it('Callback should be invoked when radio/card is pressed', () => {
        renderApp({ selectedModelTemplateId: 'yolo-id' });

        fireEvent.click(screen.getByRole('radio', { name: defaultTemplate.name }));

        expect(handleSelectedTemplateId).toHaveBeenCalledTimes(1);

        fireEvent.click(screen.getByTestId(`${idMatchingFormat(defaultTemplate.name)}-id`));

        expect(handleSelectedTemplateId).toHaveBeenCalledTimes(2);
    });

    it('Active model template should have model tag', () => {
        renderApp({});

        const templateCard = screen.getByTestId(`${defaultTemplate.name.toLocaleLowerCase()}-id`);

        expect(within(templateCard).getByText('Active model')).toBeInTheDocument();
    });

    it('Inactive model template should not have model tag', () => {
        renderApp({ selectedModelTemplateId: defaultTemplate.modelTemplateId, activeModelId: 'yolo-id' });

        const templateCard = screen.getByTestId(`${defaultTemplate.name.toLocaleLowerCase()}-id`);

        expect(within(templateCard).queryByText('Active model')).not.toBeInTheDocument();
    });

    it('Render deprecated templates', () => {
        const deprecatedTemplate = { ...defaultTemplate, lifecycleStage: LifecycleStage.DEPRECATED };
        renderApp({ template: deprecatedTemplate, selectedModelTemplateId: deprecatedTemplate.modelTemplateId });

        expect(screen.getByText('Deprecated')).toBeVisible();
    });

    it('Recommended template should show recommended label', () => {
        const recommendedTemplate = { ...defaultTemplate, performanceCategory: PerformanceCategory.BALANCE };
        renderApp({ template: recommendedTemplate, selectedModelTemplateId: recommendedTemplate.modelTemplateId });

        const templateCard = screen.getByTestId(`${defaultTemplate.name.toLocaleLowerCase()}-id`);

        expect(within(templateCard).getByText('Recommended for Balance')).toBeInTheDocument();
    });

    it('Displays template metadata', () => {
        const template = getMockedSupportedAlgorithm({ license: 'MIT', gigaflops: 4.3, modelSize: 2 });
        renderApp({ template });

        expect(screen.getByText('4.3 GFlops')).toBeVisible();
        expect(screen.getByText('2 MB')).toBeVisible();
        expect(screen.getByText('MIT')).toBeVisible();
    });
});
