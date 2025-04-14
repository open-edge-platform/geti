// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { DATASET_IMPORT_WARNING_TYPE } from '../../../core/datasets/dataset.enum';
import { DatasetImportWarning } from '../../../core/datasets/dataset.interface';
import { DatasetImportWarnings } from './dataset-import-warnings.component';

const warning: DatasetImportWarning = {
    type: DATASET_IMPORT_WARNING_TYPE.WARNING,
    affectedImages: 100,
    name: 'Some name',
    description: 'Lorem ipsum dolor sit amet',
};

describe(DatasetImportWarnings, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should properly render component header', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByText('Detected issues in the dataset')).toBeVisible();
    });

    it('should properly render warning name', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByText(/some name/i)).toBeVisible();
    });

    it('should properly render warning type', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByText('Warning - Some name')).toBeVisible();
    });

    it('should properly render error type', () => {
        render(<DatasetImportWarnings warnings={[{ ...warning, type: DATASET_IMPORT_WARNING_TYPE.ERROR }]} />);

        expect(screen.getByText('Error - Some name')).toBeVisible();
    });

    it('should not render quantity of affected images if the value is undefined', () => {
        const mockWarning: DatasetImportWarning = {
            type: DATASET_IMPORT_WARNING_TYPE.WARNING,
            affectedImages: undefined,
            name: 'Some name',
            description: 'Lorem ipsum dolor sit amet',
        };

        render(<DatasetImportWarnings warnings={[mockWarning]} />);

        expect(screen.queryByText(/affected images/i)).not.toBeInTheDocument();
    });

    it('should properly render quantity of affected images', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByText('100 affected images')).toBeVisible();
    });

    it('should not render resolve strategy if it`s no in response', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByTestId('resolve-strategy-container')).toHaveTextContent('');
    });

    it('should render resolve strategy if it`s present in response', () => {
        render(<DatasetImportWarnings warnings={[{ ...warning, resolveStrategy: 'Consectectur adispisum elit' }]} />);

        expect(screen.getByTestId('resolve-strategy-container')).toHaveTextContent('Consectectur adispisum elit');
    });

    it('should render warning (yellow) icon if warning type is WARNING', () => {
        render(<DatasetImportWarnings warnings={[warning]} />);

        expect(screen.getByTestId('alert-icon')).toBeVisible();
        expect(screen.getByTestId('alert-icon')).toHaveClass('warning');
    });

    it('should render warning (red) icon if warning type is ERROR', () => {
        render(<DatasetImportWarnings warnings={[{ ...warning, type: DATASET_IMPORT_WARNING_TYPE.ERROR }]} />);

        expect(screen.getByTestId('alert-icon')).toBeVisible();
        expect(screen.getByTestId('alert-icon')).toHaveClass('negative');
    });

    it('should properly render quantity of warnings', () => {
        render(
            <DatasetImportWarnings
                warnings={[
                    { ...warning, name: 'Warning_1' },
                    { ...warning, name: 'Warning_2' },
                ]}
            />
        );

        expect(document.querySelectorAll('.warningName')?.length).toEqual(2);

        expect(screen.getByText(/warning_1/i)).toBeVisible();
        expect(screen.getByText(/warning_2/i)).toBeVisible();
    });
});
