// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import {
    AnnotationSceneState,
    SearchRuleField,
    SearchRuleOperator,
    SearchRuleShapeType,
} from '../../../core/media/media-filter.interface';
import { getMockedLabel, mockFilterOptions } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender as render } from '../../../test-utils/project-provider-render';
import {
    concatByProperty,
    deleteLastComa,
    getAnnotationSceneByKey,
    getShapesFromText,
    getShapeTypeByKey,
} from '../utils';
import { getRuleDescription, MediaFilterChips } from './media-filter-chips.component';

const expectFormatInDocument = (field: SearchRuleField, operator: SearchRuleOperator, value: string) => {
    expect(screen.queryByText(`${getRuleDescription(field, operator)} ${value}`)).toBeInTheDocument();
};

const mockRule = {
    id: '123',
    field: SearchRuleField.MediaUploadDate,
    operator: SearchRuleOperator.Less,
    value: '2020-01-01T13:00:00.000Z',
};

describe('MediaFilterChips', () => {
    const mockLabels = [
        getMockedLabel({ id: 'label-1', name: 'label-name-1' }),
        getMockedLabel({ id: 'label-2', name: 'label-name-2' }),
        getMockedLabel({ id: 'label-3', name: 'label-name-3' }),
    ];

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders empty with empty rules', async () => {
        await render(
            <MediaFilterChips
                labels={mockLabels}
                isAnomalyProject={false}
                setMediaFilterOptions={jest.fn()}
                mediaFilterOptions={{}}
            />
        );

        expect(screen.queryByLabelText('remove rule')).not.toBeInTheDocument();
    });

    it('removes rule', async () => {
        const idToRemove = '4123';
        const mockedFilterOptions = mockFilterOptions([mockRule, { ...mockRule, id: idToRemove }]);
        const mockedSetFilterOptions = jest.fn();

        await render(
            <MediaFilterChips
                labels={mockLabels}
                isAnomalyProject={false}
                mediaFilterOptions={mockedFilterOptions}
                setMediaFilterOptions={mockedSetFilterOptions}
            />
        );

        fireEvent.click(screen.getByLabelText(`remove-rule-${idToRemove}`));

        expect(mockedSetFilterOptions).toHaveBeenCalledWith({
            condition: 'and',
            rules: [mockRule],
        });
    });

    it('invalid field or operator renders empty', async () => {
        const mockedFilterOptions = mockFilterOptions([
            {
                ...mockRule,
                field: 'test' as SearchRuleField,
                operator: 'test' as SearchRuleOperator,
                value: 50,
            },
        ]);

        await render(
            <MediaFilterChips
                labels={mockLabels}
                isAnomalyProject={false}
                mediaFilterOptions={mockedFilterOptions}
                setMediaFilterOptions={jest.fn()}
            />
        );

        const container = screen.getByLabelText(`chip-${mockRule.id}`);
        const span = container.querySelector('span') as HTMLElement;

        expect(span.textContent).toEqual(' 50');
    });

    it('normal/anomalous label chip is not visible in anomaly projects', async () => {
        const ruleId = '1234';
        const mockedFilterOptions = mockFilterOptions([
            {
                field: SearchRuleField.LabelId,
                id: ruleId,
                value: [mockLabels[0].id],
                operator: SearchRuleOperator.In,
            },
        ]);

        await render(
            <MediaFilterChips
                labels={mockLabels}
                isAnomalyProject
                mediaFilterOptions={mockedFilterOptions}
                setMediaFilterOptions={jest.fn()}
            />
        );

        expect(screen.queryByLabelText(`chip-${ruleId}`)).not.toBeInTheDocument();
    });

    describe('format and render', () => {
        it('LabelId', async () => {
            const [labelOne, labelTwo] = mockLabels;
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.LabelId,
                    operator: SearchRuleOperator.Equal,
                    value: [labelOne.id, labelTwo.id],
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(
                SearchRuleField.LabelId,
                SearchRuleOperator.Equal,
                `${labelOne.name}, ${labelTwo.name}`
            );
        });

        it('MediaUploadDate', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.MediaUploadDate,
                    operator: SearchRuleOperator.Less,
                    value: '2020-01-01T00:00:00.000Z',
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(SearchRuleField.MediaUploadDate, SearchRuleOperator.Less, 'Jan 1, 2020, 12:00 AM');
        });

        it('AnnotationSceneState', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.AnnotationSceneState,
                    operator: SearchRuleOperator.NotEqual,
                    value: AnnotationSceneState.PARTIALLY_ANNOTATED,
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(
                SearchRuleField.AnnotationSceneState,
                SearchRuleOperator.NotEqual,
                getAnnotationSceneByKey(AnnotationSceneState.PARTIALLY_ANNOTATED)?.text as string
            );
        });

        it('MediaWidth', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.MediaWidth,
                    operator: SearchRuleOperator.LessOrEqual,
                    value: 20,
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(SearchRuleField.MediaWidth, SearchRuleOperator.LessOrEqual, '20');
        });

        it('shapeAreaPercentage', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.ShapeAreaPercentage,
                    operator: SearchRuleOperator.LessOrEqual,
                    value: 0.8,
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(SearchRuleField.ShapeAreaPercentage, SearchRuleOperator.LessOrEqual, '80%');
        });

        it('shapeType with single value', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.ShapeType,
                    operator: SearchRuleOperator.Equal,
                    value: SearchRuleShapeType.POLYGON,
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(
                SearchRuleField.ShapeType,
                SearchRuleOperator.Equal,
                getShapeTypeByKey(SearchRuleShapeType.POLYGON)?.text as string
            );
        });

        it('shapeType with multiple values value', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.ShapeType,
                    operator: SearchRuleOperator.In,
                    value: [SearchRuleShapeType.POLYGON, SearchRuleShapeType.ELLIPSE],
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(
                SearchRuleField.ShapeType,
                SearchRuleOperator.In,
                deleteLastComa(
                    concatByProperty(
                        getShapesFromText([SearchRuleShapeType.POLYGON, SearchRuleShapeType.ELLIPSE]),
                        'text'
                    )
                )
            );
        });

        it('MediaHeight (default case)', async () => {
            const mockedFilterOptions = mockFilterOptions([
                {
                    ...mockRule,
                    field: SearchRuleField.MediaHeight,
                    operator: SearchRuleOperator.GreaterOrEqual,
                    value: 80,
                },
            ]);

            await render(
                <MediaFilterChips
                    labels={mockLabels}
                    isAnomalyProject={false}
                    mediaFilterOptions={mockedFilterOptions}
                    setMediaFilterOptions={jest.fn()}
                />
            );

            expectFormatInDocument(SearchRuleField.MediaHeight, SearchRuleOperator.GreaterOrEqual, '80');
        });
    });
});
